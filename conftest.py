import pytest
from app import create_app
from db import db as _db


@pytest.fixture(scope='session')
def app():
    """创建测试应用"""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def db(app):
    """创建测试数据库"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """创建测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, db):
    """创建已认证的测试客户端"""
    from db import User, UserRole

    # 创建测试用户
    user = User(
        username='testadmin',
        password='test123',
        real_name='测试管理员',
        role=UserRole.ADMIN.value
    )
    _db.session.add(user)
    _db.session.commit()

    # 登录
    client.post('/login', data={
        'username': 'testadmin',
        'password': 'test123',
        'captcha': 'test'  # 测试环境跳过验证码
    }, follow_redirects=True)

    return client