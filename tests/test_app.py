import pytest


@pytest.mark.parametrize(
    ("registered_methods", "request_method", "expected_status"),
    [
        (["GET"], "GET", "200 OK"),
        (["POST"], "POST", "200 OK"),
        (["GET"], "POST", "404 Not Found"),
        (["POST"], "GET", "404 Not Found"),
        (["GET", "POST"], "GET", "200 OK"),
        (["GET", "POST"], "POST", "200 OK"),
    ],
)
def test_route_method_matching(
    registered_methods,
    request_method,
    expected_status,
):
    app = create_app()

    @app.route("/", registered_methods)
    def handler(req: Request):
        return req.method

    body, status, headers = call_app(
        app,
        "/",
        request_method,
    )

    assert status == expected_status

    if expected_status == "200 OK":
        assert body == request_method.encode()