@Library(['codenarc@0.1.0', 'python-utils@0.3.0', 'runthebuilds@0.5.0']) _


def addStages() {
  def dtrImage = dtr.create(this, 'devtools', 'jenkins-node-scanner')
  def venv = virtualenv.create(this, 'python3.6')

  runTheBuilds.timedStage('Checkout') {
    // Print out all environment variables for debugging purposes
    sh 'env'
    checkout scm
  }

  runTheBuilds.timedStage('Setup') {
    venv.run('pip install -r requirements.txt')
    venv.run('pip install pylint flake8 yamllint pydocstyle')
  }

  runTheBuilds.timedStage('Check') {
    parallel(failFast:false,
      codenarc: {
        codenarc.check()
      },
      flake8: {
        venv.run('flake8 jenkins_node_scanner.py --max-line-length 90 -v')
      },
      pydocstyle: {
        venv.run('pydocstyle jenkins_node_scanner.py .')
      },
      pylint: {
        venv.run('pylint jenkins_node_scanner.py --max-line-length 90')
      },
      yamllint: {
        venv.run('yamllint .travis.yml')
      },
    )
  }

  runTheBuilds.timedStage('Build') {
    dtrImage.build()
  }

  if (env.HEAD_REF == 'origin/master' || env.HEAD_REF == 'refs/heads/master') {
    runTheBuilds.timedStage('Deploy') {
      dtrImage.deploy('8000', '-v jenkins-nodes:/jenkins_nodes', env.CONTAINER_ARGS)
    }
  }
}


runTheBuilds.runForSpecificBranches(runTheBuilds.COMMON_BRANCH_FILTERS, true) {
  node('generic-linux') {
    try {
      runTheBuilds.report('pending', env.CALLBACK_URL)
      addStages()
      runTheBuilds.report('success', env.CALLBACK_URL)
    } catch (error) {
      runTheBuilds.report('failure', env.CALLBACK_URL)
      throw error
    } finally {
      runTheBuilds.timedStage('Cleanup') {
        dir(env.WORKSPACE) {
          deleteDir()
        }
      }
    }
  }
}
