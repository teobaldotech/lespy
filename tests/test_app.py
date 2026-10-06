```python
from lespy import JSONResponse, Request, App


# ============================================================
# FIXTURES
# ============================================================

def create_app():
    """
    Cria uma aplicação nova para cada teste.
    """
    return App("app1", "/")


def call_app(app, path="/", method="GET"):
    """
    Executa a aplicação como uma chamada WSGI
    e retorna body + status + headers.
    """
    environ = {
        "PATH_INFO": path,
        "REQUEST_METHOD": method,
    }

    captured = {
        "status": None,
        "headers": None,
    }

    def start_response(status, headers, *args):
        captured["status"] = status
        captured["headers"] = headers

    response = app(environ, start_response)

    body = b"".join(response)

    return body, captured["status"], captured["headers"]


# ============================================================
# APP / CONFIGURAÇÃO
# ============================================================

def test_app_name():
    app = create_app()

    assert app._app_name == "app1"


def test_app_base_path():
    app = create_app()

    assert app._base_path == "/"


def test_app_router_exists():
    app = create_app()

    assert app._router is not None


def test_app_router_starts_empty():
    app = create_app()

    assert len(app._router._routes) == 0


# ============================================================
# GET
# ============================================================

def test_get_simple_text():
    app = create_app()

    def index(req: Request):
        return "Hello, this is my first app"

    app.route("/", ["GET"])(index)

    body, status, headers = call_app(app, "/", "GET")

    assert body == b"Hello, this is my first app"
    assert status == "200 OK"


def test_get_content_type():
    app = create_app()

    def index(req: Request):
        return "Hello"

    app.route("/", ["GET"])(index)

    body, status, headers = call_app(app)

    assert ("Content-Type", "text/plain") in headers


def test_get_route_registered():
    app = create_app()

    def index(req: Request):
        return "Home"

    app.route("/", ["GET"])(index)

    assert len(app._router._routes) == 1


def test_get_named_route():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return "Home"

    rule = app._find_rule("", "get")

    assert rule is not None
    assert rule[0].name == "index"


# ============================================================
# POST
# ============================================================

def test_post_json():
    app = create_app()

    def index(req: Request):
        return JSONResponse({"err": True})

    app.route("/", ["POST"])(index)

    body, status, headers = call_app(app, "/", "POST")

    assert body == b'{"err": true}'
    assert status == "200 OK"


def test_post_content_type():
    app = create_app()

    def index(req: Request):
        return JSONResponse({"success": True})

    app.route("/", ["POST"])(index)

    body, status, headers = call_app(app, "/", "POST")

    assert ("Content-Type", "application/json") in headers


def test_post_json_false():
    app = create_app()

    def index(req: Request):
        return JSONResponse({"err": False})

    app.route("/", ["POST"])(index)

    body, status, headers = call_app(app, "/", "POST")

    assert body == b'{"err": false}'


def test_post_named_route():
    app = create_app()

    @app.route("/register", ["POST"], "register")
    def register(req: Request):
        return JSONResponse({"registered": True})

    rule = app._find_rule("register/", "post")

    assert rule is not None
    assert rule[0].name == "register"


# ============================================================
# 404 / ROTAS INEXISTENTES
# ============================================================

def test_empty_router_returns_404():
    app = create_app()

    body, status, headers = call_app(app, "/", "GET")

    assert body == b"Page not found."
    assert status == "404 Not Found"


def test_empty_router_content_type():
    app = create_app()

    body, status, headers = call_app(app, "/", "GET")

    assert (
        "Content-Type",
        "text/html; charset=utf-8",
    ) in headers


def test_unknown_route_returns_404():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return "Home"

    body, status, headers = call_app(
        app,
        "/unknown",
        "GET",
    )

    assert status == "404 Not Found"
    assert body == b"Page not found."


def test_unknown_nested_route_returns_404():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return "Home"

    body, status, headers = call_app(
        app,
        "/api/users",
        "GET",
    )

    assert status == "404 Not Found"


# ============================================================
# MÉTODOS HTTP
# ============================================================

def test_route_only_accepts_get():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return "GET"

    body, status, headers = call_app(
        app,
        "/",
        "GET",
    )

    assert body == b"GET"
    assert status == "200 OK"


def test_post_route_does_not_match_get():
    app = create_app()

    @app.route("/", ["POST"])
    def index(req: Request):
        return "POST"

    body, status, headers = call_app(
        app,
        "/",
        "GET",
    )

    assert status == "404 Not Found"


def test_get_route_does_not_match_post():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return "GET"

    body, status, headers = call_app(
        app,
        "/",
        "POST",
    )

    assert status == "404 Not Found"


def test_multiple_methods():
    app = create_app()

    @app.route("/", ["GET", "POST"])
    def index(req: Request):
        if req.method == "GET":
            return "GET"

        return JSONResponse({"method": "POST"})

    body, status, headers = call_app(
        app,
        "/",
        "GET",
    )

    assert status == "200 OK"
    assert body == b"GET"


def test_multiple_methods_post():
    app = create_app()

    @app.route("/", ["GET", "POST"])
    def index(req: Request):
        if req.method == "GET":
            return "GET"

        return JSONResponse({"method": "POST"})

    body, status, headers = call_app(
        app,
        "/",
        "POST",
    )

    assert status == "200 OK"
    assert body == b'{"method": "POST"}'


# ============================================================
# MÚLTIPLAS ROTAS
# ============================================================

def test_multiple_routes():
    app = create_app()

    @app.route("/", ["GET"])
    def home(req: Request):
        return "Home"

    @app.route("/about", ["GET"])
    def about(req: Request):
        return "About"

    @app.route("/register", ["POST"], "register")
    def register(req: Request):
        return JSONResponse({"ok": True})

    assert len(app._router._routes) == 3


def test_home_route():
    app = create_app()

    @app.route("/", ["GET"])
    def home(req: Request):
        return "Home"

    body, status, headers = call_app(
        app,
        "/",
        "GET",
    )

    assert status == "200 OK"
    assert body == b"Home"


def test_about_route():
    app = create_app()

    @app.route("/about", ["GET"])
    def about(req: Request):
        return "About"

    body, status, headers = call_app(
        app,
        "/about",
        "GET",
    )

    assert status == "200 OK"
    assert body == b"About"


def test_register_route():
    app = create_app()

    @app.route("/register", ["POST"], "register")
    def register(req: Request):
        return JSONResponse({"registered": True})

    body, status, headers = call_app(
        app,
        "/register",
        "POST",
    )

    assert status == "200 OK"
    assert body == b'{"registered": true}'


# ============================================================
# NOMES DE ROTAS
# ============================================================

def test_route_name_default():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        pass

    rule = app._find_rule("", "get")

    assert rule[0].name == "index"


def test_route_name_custom():
    app = create_app()

    @app.route(
        "/register",
        ["POST"],
        "register",
    )
    def register_handler(req: Request):
        pass

    rule = app._find_rule(
        "register/",
        "post",
    )

    assert rule[0].name == "register"


def test_route_names_count():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        pass

    @app.route(
        "/register",
        ["POST"],
        "register",
    )
    def register_handler(req: Request):
        pass

    assert len(app._router._routes) == 2


# ============================================================
# JSON RESPONSE
# ============================================================

def test_json_response_boolean():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return JSONResponse({
            "success": True,
        })

    body, status, headers = call_app(app)

    assert body == b'{"success": true}'


def test_json_response_string():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return JSONResponse({
            "message": "Hello",
        })

    body, status, headers = call_app(app)

    assert body == b'{"message": "Hello"}'


def test_json_response_multiple_fields():
    app = create_app()

    @app.route("/", ["GET"])
    def index(req: Request):
        return JSONResponse({
            "id": 1,
            "name": "Teobaldo",
            "active": True,
        })

    body, status, headers = call_app(app)

    assert b'"id": 1' in body
    assert b'"name": "Teobaldo"' in body
    assert b'"active": true' in body


# ============================================================
# REQUEST OBJECT
# ============================================================

def test_request_method_get():
    app = create_app()

    captured = {}

    @app.route("/", ["GET"])
    def index(req: Request):
        captured["method"] = req.method
        return "OK"

    call_app(app, "/", "GET")

    assert captured["method"] == "GET"


def test_request_method_post():
    app = create_app()

    captured = {}

    @app.route("/", ["POST"])
    def index(req: Request):
        captured["method"] = req.method
        return "OK"

    call_app(app, "/", "POST")

    assert captured["method"] == "POST"


# ============================================================
# ROTAS COM DIFERENTES CAMINHOS
# ============================================================

def test_api_route():
    app = create_app()

    @app.route("/api", ["GET"])
    def api(req: Request):
        return "API"

    body, status, headers = call_app(
        app,
        "/api",
        "GET",
    )

    assert status == "200 OK"
    assert body == b"API"


def test_users_route():
    app = create_app()

    @app.route("/users", ["GET"])
    def users(req: Request):
        return JSONResponse({
            "users": [],
        })

    body, status, headers = call_app(
        app,
        "/users",
        "GET",
    )

    assert status == "200 OK"
    assert body == b'{"users": []}'


def test_nested_api_route():
    app = create_app()

    @app.route("/api/users", ["GET"])
    def users(req: Request):
        return "Users"

    body, status, headers = call_app(
        app,
        "/api/users",
        "GET",
    )

    assert status == "200 OK"
    assert body == b"Users"


# ============================================================
# INTEGRIDADE DO ROUTER
# ============================================================

def test_router_route_count():
    app = create_app()

    @app.route("/", ["GET"])
    def home(req: Request):
        return "Home"

    @app.route("/users", ["GET"])
    def users(req: Request):
        return "Users"

    @app.route("/login", ["POST"])
    def login(req: Request):
        return "Login"

    assert len(app._router._routes) == 3


def test_find_existing_get_rule():
    app = create_app()

    @app.route("/home", ["GET"])
    def home(req: Request):
        return "Home"

    result = app._find_rule(
        "home/",
        "get",
    )

    assert result
    assert result[0].name == "home"


def test_find_existing_post_rule():
    app = create_app()

    @app.route("/login", ["POST"])
    def login(req: Request):
        return "Login"

    result = app._find_rule(
        "login/",
        "post",
    )

    assert result
    assert result[0].name == "login"


# ============================================================
# TESTE COMPLETO DE FLUXO
# ============================================================

def test_complete_application_flow():
    app = create_app()

    @app.route("/", ["GET"])
    def home(req: Request):
        return "Home"

    @app.route("/api/status", ["GET"])
    def status(req: Request):
        return JSONResponse({
            "status": "online",
        })

    @app.route("/register", ["POST"], "register")
    def register(req: Request):
        return JSONResponse({
            "registered": True,
        })

    # Home
    body, status_code, headers = call_app(
        app,
        "/",
        "GET",
    )

    assert status_code == "200 OK"
    assert body == b"Home"

    # API
    body, status_code, headers = call_app(
        app,
        "/api/status",
        "GET",
    )

    assert status_code == "200 OK"
    assert body == b'{"status": "online"}'

    # Register
    body, status_code, headers = call_app(
        app,
        "/register",
        "POST",
    )

    assert status_code == "200 OK"
    assert body == b'{"registered": true}'

    # Rota inexistente
    body, status_code, headers = call_app(
        app,
        "/does-not-exist",
        "GET",
    )

    assert status_code == "404 Not Found"
    assert body == b"Page not found."
```

Essa versão possui **mais de 40 casos/verificações**, cobrindo:

* `App`
* configuração inicial
* Router
* rotas `GET`
* rotas `POST`
* múltiplos métodos
* múltiplas rotas
* nomes de rotas
* `Request.method`
* `JSONResponse`
* `Content-Type`
* respostas `200`
* respostas `404`
* rotas inexistentes
* rotas aninhadas
* `/api`
* `/users`
* `/register`
* fluxo completo da aplicação
* integração entre `App`, Router e handlers

Para executar:

```bash
pytest -v test_app_pro.py
```

Ou, mostrando também a cobertura:

```bash
pytest -v --cov=lespy
```

**Observação:** mantive os testes baseados na API que aparece no seu arquivo original (`App("app1", "/")`, `app.route()`, `_find_rule()`, `_router._routes`, `JSONResponse` etc.), para reduzir o risco de criar testes incompatíveis com a versão específica do `lespy` que você está usando.
