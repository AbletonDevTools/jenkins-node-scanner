library 'ableton-utils@0.13'
library 'groovylint@0.6'
library 'python-utils@0.9'


devToolsProject.run(
  setup: { data ->
    data['dtrImage'] = dtr.create('devtools', 'jenkins-node-scanner')
    data['venv'] = virtualenv.create('python3.7')
    data.venv.run('pip install -r requirements-dev.txt -r requirements.txt')
  },
  build: { data ->
    Map creds = encryptedFile.readJson(
      path: 'credentials.json.enc',
      credentialsId: 'jenkins-node-scanner-password',
    )

    String jinjaCommand = "jinja2 -D host=${creds['host']} -D port=${creds['port']}"
    data.venv.run("${jinjaCommand} -o papertrail_config.yml papertrail_config.yml.j2")

    String cliArgs = encryptedFile.read(
      path: 'cli-args.enc',
      credentialsId: 'jenkins-node-scanner-password',
    ).trim()
    data.venv.run("${jinjaCommand} -D args='${cliArgs}'" +
      ' -o supervisord.conf supervisord.conf.j2')

    data.dtrImage.build()
  },
  test: { data ->
    parallel(failFast: false,
      black: {
        data.venv.run('black --check .')
      },
      flake8: {
        data.venv.run('flake8 -v')
      },
      groovylint: {
        groovylint.check('./Jenkinsfile')
      },
      hadolint: {
        docker.image('hadolint/hadolint:v1.13.0-debian').inside("-v ${pwd()}:/ws") {
          sh 'hadolint /ws/Dockerfile'
        }
      },
      pydocstyle: {
        data.venv.run('pydocstyle -v')
      },
      pylint: {
        data.venv.run('pylint jenkins_node_scanner.py')
      },
    )
  },
  deployWhen: { return runTheBuilds.isPushTo(['master']) || env.FORCE_DEPLOY == 'true' },
  deploy: { data ->
    data.dtrImage.push()
    data.dtrImage.deploy('8000', '-v jenkins-nodes:/jenkins_nodes')
  },
  cleanup: { data ->
    data.venv?.cleanup()
  },
)
