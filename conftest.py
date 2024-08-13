import pytest
import allure
import uuid



@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=DEBUG')

    return chrome_options


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Эта функция помогает обнаружить, что какой-то тест не удался
    # и передаёт эту информацию в teardown:

    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
    return rep


@pytest.fixture
def web_browser(request, selenium):

    browser = selenium
    browser.set_window_size(1400, 1000)

    # Вернуть экземпляр браузера в тест-кейс:
    yield browser

    # teardown (этот код будет выполняться после каждого теста):

    if request.node.rep_call.failed:
        # Сделать снимок экрана, если тест не удался:
        try:
            browser.execute_script("document.body.bgColor = 'white';")

            # Сделать снимок экрана для локальной отладки:
            browser.save_screenshot('screenshots/' + str(uuid.uuid4()) + '.png')

            # Прикрепить скриншот к отчету Allure:
            allure.attach(browser.get_screenshot_as_png(),
                          name=request.function.__name__,
                          attachment_type=allure.attachment_type.PNG)

            print('URL: ', browser.current_url)
            print('Browser logs:')
            for log in browser.get_log('browser'):
                print(log)

        except:
            pass


def get_test_case_docstring(item):
    """ Эта функция получает строку документа из тестового примера и форматирует ее,
        чтобы показывать эту строку документа вместо имени тестового примера в отчетах.
    """

    full_name = ''

    if item._obj.__doc__:
        # Remove extra whitespaces from the doc string:
        name = str(item._obj.__doc__.split('.')[0]).strip()
        full_name = ' '.join(name.split())

        # Generate the list of parameters for parametrized test cases:
        if hasattr(item, 'callspec'):
            params = item.callspec.params

            res_keys = sorted([k for k in params])
            # Create List based on Dict:
            res = ['{0}_"{1}"'.format(k, params[k]) for k in res_keys]
            # Add dict with all parameters to the name of test case:
            full_name += ' Parameters ' + str(', '.join(res))
            full_name = full_name.replace(':', '')

    return full_name


def pytest_itemcollected(item):
    """ Эта функция изменяет названия тестовых примеров "на ходу"
        во время выполнения тестовых случаев.
    """

    if item._obj.__doc__:
        item._nodeid = get_test_case_docstring(item)


def pytest_collection_finish(session):
    """ Эта функция изменяет имена тестовых примеров "на ходу",
        когда мы используем параметр --collect-only для pytest
        (чтобы получить полный список всех существующих тестовых примеров).
    """

    if session.config.option.collectonly is True:
        for item in session.items:
            if item._obj.__doc__:
                full_name = get_test_case_docstring(item)
                print(full_name)

        pytest.exit('Done!')