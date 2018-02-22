@SuppressWarnings('VariableTypeRequired') // For _ variable
@Library(['ableton-utils@0.6.0', 'groovylint@0.3.0', 'python-utils@0.3.0']) _

import com.ableton.VirtualEnv as VirtualEnv


runTheBuilds.runDevToolsProject(
  setup: { data ->
    data['dtrImage'] = dtr.create(this, 'devtools', 'jenkins-node-scanner')
    VirtualEnv venv = virtualenv.create(this, 'python3.6')
    venv.run('pip install -r requirements.txt')
    venv.run('pip install pylint flake8 yamllint pydocstyle')
    data['venv'] = venv
  },
  build: { data ->
    data['dtrImage'].build()
  },
  test: { data ->
    VirtualEnv venv = data['venv']
    parallel(failFast: false,
      flake8: {
        venv.run('flake8 jenkins_node_scanner.py --max-line-length 90 -v')
      },
      groovylint: {
        groovylint.check('./Jenkinsfile')
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
  },
  deploy: { data ->
    runTheBuilds.runForSpecificBranches(['master'], false) {
      data['dtrImage'].push()
      data['dtrImage'].deploy(
        '8000', '-v jenkins-nodes:/jenkins_nodes', env.CONTAINER_ARGS)
    }
  },
)
