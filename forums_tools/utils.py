from requests_html import HTMLSession


def get_thread_global(f, link):
    if session_global is not None:
        session = session_global
    f(link, session)


def initialize_worker():
    global session_global
    session_global = HTMLSession()


def get_html_session(session=None):
    if session is None:
        print("new html session")
        return HTMLSession()
    else:
        return session
