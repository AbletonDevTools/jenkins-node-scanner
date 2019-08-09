library 'ableton-utils@0.13'
library 'groovylint@0.6'


devToolsProject.run(
  setup: { data ->
    data['dtrImage'] = dtr.create('devtools', 'jenkins-node-scanner')
    sh 'pipenv sync --dev'
  },
  build: { data ->
    Map creds = encryptedFile.readJson(
      path: 'credentials.json.enc',
      credentialsId: 'jenkins-node-scanner-password',
    )
    String jinjaCommand = "jinja2 -D host=${creds['host']} -D port=${creds['port']}"
    ['papertrail_config.yml', 'supervisord.conf'].each { file ->
      sh "pipenv run ${jinjaCommand} -o ${file} ${file}.j2"
    }

    data['dtrImage'].build()
  },
  test: {
    parallel(failFast: false,
      black: {
        sh 'pipenv run black --check .'
      },
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
    String cliArgs = encryptedFile.read(
      path: 'cli-args.enc',
      credentialsId: 'jenkins-node-scanner-password',
    ).trim()

    data['dtrImage'].deploy('8000', '-v jenkins-nodes:/jenkins_nodes', cliArgs)
  },
  cleanup: {
    try {
      sh 'pipenv --rm'
    } catch (ignored) {}
  },
)
