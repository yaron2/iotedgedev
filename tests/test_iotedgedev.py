import pytest
import os
import shutil

import click
from click.testing import CliRunner
from iotedgedev.envvars import EnvVars
from iotedgedev.output import Output
# from iotedgedev import cli

root_dir = os.getcwd()
tests_dir = os.path.join(root_dir, "tests")
env_file = os.path.join(root_dir, ".env")
test_solution = "test_solution"
node_solution = "node_solution"
test_solution_dir = os.path.join(tests_dir, test_solution)
node_solution_dir = os.path.join(tests_dir, node_solution)


@pytest.fixture(scope="module", autouse=True)
def create_solution(request):

    cli = __import__("iotedgedev.cli", fromlist=['main'])
    # print cli
    # out, err = capsys.readouterr()
    # print out

    runner = CliRunner()
    os.chdir(tests_dir)
    result = runner.invoke(cli.main, ['solution', test_solution])
    print (result.output)
    assert 'AZURE IOT EDGE SOLUTION CREATED' in result.output

    shutil.copyfile(env_file, os.path.join(test_solution_dir, '.env'))
    os.chdir(test_solution_dir)

    def clean():
        os.chdir(root_dir)
        shutil.rmtree(test_solution_dir, ignore_errors=True)
    request.addfinalizer(clean)
    return


@pytest.fixture
def test_push_modules(request):

    os.chdir(test_solution_dir)

    cli = __import__("iotedgedev.cli", fromlist=['main'])
    runner = CliRunner()
    result = runner.invoke(cli.main, ['push'])
    print (result.output)

    assert 'BUILD COMPLETE' in result.output
    assert 'PUSH COMPLETE' in result.output


@pytest.fixture
def test_deploy_modules(request):

    os.chdir(test_solution_dir)

    cli = __import__("iotedgedev.cli", fromlist=['main'])
    runner = CliRunner()
    result = runner.invoke(cli.main, ['deploy'])
    print (result.output)

    assert 'DEPLOYMENT COMPLETE' in result.output


@pytest.fixture
def test_start_runtime(request):

    os.chdir(test_solution_dir)

    cli = __import__("iotedgedev.cli", fromlist=['main'])
    runner = CliRunner()
    result = runner.invoke(cli.main, ['start'])
    print (result.output)

    assert 'Runtime started' in result.output


@pytest.fixture
def test_monitor(request, capfd):

    os.chdir(test_solution_dir)

    cli = __import__("iotedgedev.cli", fromlist=['main'])
    runner = CliRunner()
    result = runner.invoke(cli.main, ['monitor', '--timeout', '40000'])
    out, err = capfd.readouterr()
    print (out)
    print (err)
    print (result.output)

    assert 'application properties' in out


@pytest.fixture
def test_stop(request):

    os.chdir(test_solution_dir)

    cli = __import__("iotedgedev.cli", fromlist=['main'])
    runner = CliRunner()
    result = runner.invoke(cli.main, ['stop'])
    print (result.output)

    assert 'Runtime stopped' in result.output


def test_e2e(test_push_modules, test_deploy_modules, test_start_runtime, test_monitor, test_stop):
    print ('Testing E2E')


@pytest.fixture
def setup_node_solution(request):

    shutil.copyfile(env_file, os.path.join(node_solution_dir, '.env'))
    os.chdir(node_solution_dir)

    def clean():
        os.chdir(root_dir)
    request.addfinalizer(clean)
    return


def test_node(setup_node_solution, test_push_modules, test_deploy_modules, test_start_runtime, test_monitor, test_stop):
    print ('Testing Node Solution')


'''
def test_load_no_dotenv():

    dotenv_file = ".env.nofile"
    os.environ["DOTENV_FILE"] = dotenv_file

    # cli_inst =
    # runner = CliRunner()
    # result = runner.invoke(cli.main, ['--set-config'])
    # print result.output
    # assert result.exit_code == 0
    # assert '.env.test file not found on disk.' in result.output
    # assert 'PROCESSING' in result.output
'''
