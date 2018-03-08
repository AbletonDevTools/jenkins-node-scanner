@SuppressWarnings('VariableTypeRequired') // For _ variable
@Library([
  'ableton-utils@0.8',
  'groovylint@0.3',
  'python-utils@0.8',
]) _

import com.ableton.VirtualEnv as VirtualEnv


runTheBuilds.runDevToolsProject(
  setup: { data ->
    data['dtrImage'] = dtr.create('devtools', 'jenkins-node-scanner')
    VirtualEnv venv = virtualenv.create('python3.6')
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
      hadolint: {
        docker.image('hadolint/hadolint').inside("-v ${pwd()}:/ws") {
          sh 'hadolint /ws/Dockerfile'
        }
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
