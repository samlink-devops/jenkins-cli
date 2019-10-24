from jenkinsapi.jenkins import Jenkins
from six.moves.urllib.parse import urlparse
from os.path import expanduser
from os import path
from getpass import getuser
from sys import stdout

import argparse
import yaml
import json

def main():
  parser = argparse.ArgumentParser(description='Jenkins CLI')

  parser.add_argument('--endpoint', '-e', dest='endpoint', type=str,
                    required=True,
                    help='api endpoint')
  parser.add_argument('--user', '-u', dest='username', type=str,
                    default=getuser(),
                    help='username (default: %s)' % getuser())
  parser.add_argument('--key-file', '-kf', dest='key_file', type=str,
                    help='location of api key (default: ~/.jenkins/<endpoint-hostname>.key)')
  parser.add_argument('--ca-cert', '-ca', dest='ca_bundle', type=str,
                    default=get_ca_bundle(),
                    help='certificate bundle (default: %s)' % get_ca_bundle())
  parser.add_argument('--unsafe', dest='unsafe', action='store_true',
                    help='disable ssl verification')
  parser.add_argument('--silent', '-s', dest='silent', action='store_true',
                    help='enable silent operation')

  subparsers = parser.add_subparsers()

  # Job sub-commands
  parser_job = subparsers.add_parser('job', description='jobs')
  job_subparser = parser_job.add_subparsers()

  # List jobs
  parser_job_list = job_subparser.add_parser('list', description='list jobs')
  parser_job_list.set_defaults(func=job_list)

  # Start job
  parser_job_start = job_subparser.add_parser('start', description='start job')
  parser_job_start.add_argument('--job-name', '-j', dest='job_name', type=str,
                             required=True,
                             help='job name')
  parser_job_start.add_argument('--yaml-param-file', dest='yaml_param_file', type=argparse.FileType('r'),
                             help='location of yaml formatted parameter file')
  parser_job_start.add_argument('--json-param-file', dest='json_param_file', type=argparse.FileType('r'),
                             help='location of json formatted parameter file')
  parser_job_start.add_argument('--no-wait', dest='wait_started', action='store_false',
                             help='do not wait')
  parser_job_start.add_argument('--wait-completed', dest='wait_completed', action='store_true',
                             help='wait until completed')
  parser_job_start.add_argument('--console', dest='console', action='store_true',
                             help='enable jenkins console output (default: disabled)')
  parser_job_start.add_argument('--console-output', dest='console_output', type=argparse.FileType('a'),
                             default=stdout,
                             help='write jenkins console output to file (default: stderr)')
  parser_job_start.add_argument('--quiet-period', dest='quiet_period', type=int,
                             required=False, default=0,
                             help='quiet period in seconds (default: 0)')
  parser_job_start.add_argument('--wait-delay', dest='wait_delay', type=int,
                             required=False, default=5,
                             help='delay in milliseconds between requests (default: 5)')
  parser_job_start.set_defaults(func=job_start)

  # Get job builds
  parser_job_builds = job_subparser.add_parser('builds', description='list builds')
  parser_job_builds.add_argument('--job-name', '-j', dest='job_name', type=str,
                             required=True,
                             help='job name')
  parser_job_builds.set_defaults(func=job_builds)

  # Describe job
  parser_job_describe = job_subparser.add_parser('desc', description='job description')
  parser_job_describe.add_argument('--job-name', '-j', dest='job_name', type=str,
                             required=True,
                             help='job name')
  parser_job_describe.set_defaults(func=job_desc)

  # Get job params
  parser_job_params = job_subparser.add_parser('params', description='job parameters')
  parser_job_params.add_argument('--job-name', '-j', dest='job_name', type=str,
                             required=True,
                             help='job name')
  parser_job_params.set_defaults(func=job_params)

  # Get job console output
  parser_job_build_console = job_subparser.add_parser('console', description='get console output')
  parser_job_build_console.add_argument('--job-name', '-j', dest='job_name', type=str,
                             required=True,
                             help='job name')
  parser_job_build_console.add_argument('--build-number', '-b', dest='build_number', type=int,
                             required=True,
                             help='build number')
  parser_job_build_console.add_argument('--no-streaming', dest='disable_streaming', action='store_true',
                             help='disable console streaming')
  parser_job_build_console.set_defaults(func=job_build_console)

  args = parser.parse_args()

  process_result(args, args.func(args))

def process_result(args, content):
  """ Process result """
  if content and not args.silent:
    print(json.dumps(content, indent=4, sort_keys=True))

def connect(args, lazy=False):
  """ Connect """
  return Jenkins(args.endpoint,
                 ssl_verify=args.ca_bundle if not args.unsafe else False,
                 username=args.username,
                 password=get_password(args), lazy=lazy)

def get_ca_bundle():
  """ Get certificate bundle """
  for ca in ['/etc/ssl/certs/ca-certificates.crt', '/etc/ssl/certs/ca-bundle.crt']:
    if path.isfile(ca):
      return ca
  return None

def get_password(args):
  """ Get password """
  if args.key_file:
    filename = args.key_file
  else:
    filename = expanduser('~/.jenkins/%s' % urlparse(args.endpoint).netloc)

  try:
    with open(filename) as f:
      return f.read().strip()
  except:
    print "Could not open keyfile: %s" % filename
    raise

def get_job_url(jenkins, job_name):
  """ This is a hack, that adds folders to job name """
  return '%s/%s' % (
    jenkins.baseurl,
    '/'.join(['job/%s' % part for part in job_name.split('/')]))

def get_job(jenkins, job_name):
  """ Get specific job """
  return jenkins.get_job_by_url(
    get_job_url(jenkins, job_name),
    job_name)

def job_list(args):
  """ List all available jobs """
  return connect(args).get_jobs_list()

def job_start(args):
  """ Start job """
  # We have to access internal _data for job, to get return values :-(
  job = get_job(connect(args, True), args.job_name)
  qi = job.invoke(
          block=False,
          build_params=build_params(job, args))

  if args.wait_completed or args.wait_started:
    build = qi.block_until_building(args.wait_delay)
    if args.console:
      # Write to console
      for content in build.stream_logs(interval = 1):
        args.console_output.write(content)
        args.console_output.flush()

    if args.wait_completed:
      build.block_until_complete(args.wait_delay)

    return build._data

  return qi._data

def build_params(job, args):
  if args.yaml_param_file:
    params = yaml.safe_load(args.yaml_param_file)
  elif args.json_param_file:
    params = json.load(args.json_param_file)
  else:
    params = {}
  # Unfortunaly API doesn't support quiet period properly
  # Option should be added for invoke..
  if not job.has_params():
    return params
  return add_delay_param(params, args.quiet_period)

def add_delay_param(params, delay):
  new_params = dict(params)
  new_params['delay'] = '%isec' % delay
  return new_params

def job_desc(args):
  # Again access internal data
  """ Show job description """
  return get_job(connect(args, True), args.job_name)._data

def job_params(args):
  """ Show job parameters """
  return list(get_job(connect(args, True), args.job_name).get_params())

def job_builds(args):
  """ Show builds for job """
  return get_job(connect(args, True), args.job_name).get_build_dict()

def get_build(jenkins, job_name, build_number):
  """ Show specific build for job """
  return get_job(jenkins, job_name).get_build(build_number)

def job_build_console(args):
  """ Show build console """
  build = get_build(connect(args, True), args.job_name, args.build_number)

  if not args.disable_streaming:
    for content in build.stream_logs(interval = 1):
      print content
  else:
    print build.get_console()

  return None

if __name__== "__main__":
  main()
