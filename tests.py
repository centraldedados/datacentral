import os
import shutil

TEST_OUTPUT_PATH = "_testoutput"
TEST_REPO_PATH = "_testrepos"
theme_dir = 'themes/centraldedados/'


def setup_module():
    from datacentral import generate
    generate(False, False, TEST_OUTPUT_PATH, theme_dir, TEST_REPO_PATH)


def teardown_module():
    shutil.rmtree(TEST_OUTPUT_PATH)
    shutil.rmtree(TEST_REPO_PATH)


def test_output_dir_created():
    assert os.path.exists(TEST_OUTPUT_PATH)


def test_api_created():
    assert os.path.exists(os.path.join(TEST_OUTPUT_PATH, 'api.json'))


def test_staticfiles_created():
    # only checks for one file in each asset dir, lazy :p
    assert os.path.exists(os.path.join(TEST_OUTPUT_PATH, 'css/main.css'))
    assert os.path.exists(os.path.join(TEST_OUTPUT_PATH, 'js/search.js'))
    assert os.path.exists(os.path.join(TEST_OUTPUT_PATH, 'img/ajax-loader.gif'))
