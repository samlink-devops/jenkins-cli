# jenkins-cli
jenkins-cli is a simple jenkinsapi (https://pypi.org/project/jenkinsapi/)
based command line interface (cli) for jenkins

This tool is not intended for performing administrative tasks. Use Jenkins
configuration as code plugin for managing your configuration

# Basic jenkins-cli usage
Get help:

```bash
jenkins_cli.py -h
```

Get more help:

```bash
jenkins_cli.py job -h
```

Get even more help:

```bash
jenkins_cli.py job start -h
```

Get list of jobs:

```bash
jenkins_cli.py -e https://myjenkins/ job list
```

Start a build with console output (and suppress json return value):

```bash
jenkins_cli.py -s -e https://myjenkins/ job start -j my_job --console
```
