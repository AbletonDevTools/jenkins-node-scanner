library 'ableton-utils@0.13'
library 'groovylint@0.6'


devToolsProject.run(
  setup: { data ->
    data['dtrImage'] = dtr.create('devtools', 'jenkins-node-scanner')
    sh 'pipenv sync --dev'
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
  deployWhen: { return runTheBuilds.isPushTo(['master']) || env.FORCE_DEPLOY == 'true' },
  deploy: { data ->
    data['dtrImage'].push()
    data['dtrImage'].deploy(
      '8000',
      '-v jenkins-nodes:/jenkins_nodes',
      '--target-port 9100 --target-port 9323' +
        " --url ${env.JENKINS_URL} /jenkins_nodes/output.json",
    )
  },
  cleanup: {
    try {
      sh 'pipenv --rm'
    } catch (ignored) {}
  },
)
