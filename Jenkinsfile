@Library([
  'ableton-utils@0.10',
  'groovylint@0.4',
]) _


runTheBuilds.runDevToolsProject(
  setup: { data ->
    data['dtrImage'] = dtr.create('devtools', 'jenkins-node-scanner')
    sh 'pipenv install --dev'
  },
  build: { data ->
    data['dtrImage'].build()
  },
  test: {
    parallel(failFast: false,
      flake8: {
        sh 'pipenv run flake8 -v'
      },
      groovylint: {
        groovylint.check('./Jenkinsfile')
      },
      hadolint: {
        docker.image('hadolint/hadolint:v1.13.0-debian').inside("-v ${pwd()}:/ws") {
          // DL3013: Pin versions in pip
          // We are only using pip to install pipenv, and we always want the latest and
          // greatest version for that.
          sh 'hadolint --ignore DL3013 /ws/Dockerfile'
        }
      },
      pipenv: {
        sh 'pipenv check'
      },
      pydocstyle: {
        sh 'pipenv run pydocstyle -v'
      },
      pylint: {
        sh 'pipenv run pylint jenkins_node_scanner.py'
      },
    )
  },
  deploy: { data ->
    runTheBuilds.withBranches(branches: ['master'], acceptPullRequests: false) {
      data['dtrImage'].push()
      data['dtrImage'].deploy(
        '8000', '-v jenkins-nodes:/jenkins_nodes', env.CONTAINER_ARGS)
    }
  },
  cleanup: {
    try {
      sh 'pipenv --rm'
    } catch (ignored) {}
  },
)
