from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort, make_response
from functools import wraps
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_caching import Cache
from db import db, User, Student, Department, Major, Grade, Class, StudentStatus, StudentStatusChange, MajorTransfer, Department, Major, Class, StudentStatusChange, MajorTransfer, StudentStatus
from get_captcha import get_captcha_code_and_content
from datetime import datetime
import os
from flask import jsonify
from celery_worker import make_celery
from tasks import send_status_change_notification, send_transfer_result_notification, batch_import_students, send_grade_report
from logging_config import setup_logging
from config import config

# 初始化扩展
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()
celery = None


def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    migrate.init_app(app, db)
    cache.init_app(app)

    # 初始化Celery
    global celery
    celery = make_celery(app)

    # 初始化日志
    setup_logging(app)

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app


# 创建应用实例
app = create_app(os.environ.get('FLASK_ENV', 'development'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('需要管理员权限！', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'teacher']:
            flash('需要教师权限！', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('需要学生权限！', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def check_student_owner(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        student_id = kwargs.get('id')
        if not student_id:
            abort(404)
            
        student = Student.query.get_or_404(student_id)
        if current_user.role == 'student' and student.user_id != current_user.id:
            flash('您只能查看和编辑自己的信息！', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('students'))
    return redirect(url_for('login'))


@app.route('/health')
@cache.cached(timeout=60)
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            captcha = request.form.get('captcha')
            stored_captcha = session.get('captcha', '')

            app.logger.info(f'登录尝试: username={username}')

            if not captcha or captcha.lower() != stored_captcha.lower():
                app.logger.warning(f'验证码错误: username={username}')
                flash('验证码错误！', 'danger')
                return redirect(url_for('login'))

            user = User.query.filter_by(username=username).first()

            if user is None:
                app.logger.warning(f'用户不存在: username={username}')
                flash('用户不存在！', 'danger')
                return redirect(url_for('login'))

            if user.password == password:
                login_user(user)
                app.logger.info(f'登录成功: username={username}, role={user.role}')
                flash('登录成功！', 'success')
                session.pop('captcha', None)  # 清除验证码
                  # 根据角色重定向到不同页面
                if user.is_admin():
                    return redirect(url_for('departments'))
                elif user.is_teacher():
                    return redirect(url_for('classes'))
                else:
                    # 检查用户是否有关联的学生资料
                    student = Student.query.filter_by(user_id=user.id).first()
                    if student:
                        return redirect(url_for('student_detail', id=student.id))
                    else:
                        flash('您的账号未关联学生信息，请联系管理员！', 'warning')
                        return redirect(url_for('index'))
                
            flash('密码错误！', 'danger')
            return redirect(url_for('login'))
            
        except Exception as e:
            import traceback
            app.logger.error(f'登录异常: {str(e)}\n{traceback.format_exc()}')
            db.session.rollback()
            flash('系统错误，请稍后重试！', 'danger')
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证学号是否存在且未注册
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            flash('该学号未在系统中录入，请联系管理员！', 'danger')
            return redirect(url_for('register'))
            
        # 检查是否已有关联的用户账号
        if student.user_id:
            existing_user = User.query.get(student.user_id)
            if existing_user:
                flash('该学号已注册账号，请直接登录！', 'danger')
                return redirect(url_for('login'))
        
        # 检查密码确认
        if password != confirm_password:
            flash('两次输入的密码不一致！', 'danger')
            return redirect(url_for('register'))
        
        # 检查是否有重复的用户名
        if User.query.filter_by(username=student_id).first():
            flash('该学号已被注册为用户名，请联系管理员！', 'danger')
            return redirect(url_for('register'))
              # 开启事务注册新用户
        try:
            new_user = User(
                username=student_id,
                password=password,
                real_name=student.name,
                role='student'
            )
            db.session.add(new_user)
            db.session.flush()  # 获取new_user.id
            
            # 更新学生记录的user_id并建立关系
            student.user_id = new_user.id
            student.user = new_user
            db.session.add(student)
            db.session.commit()
            
            flash('账号注册成功，请登录！', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请重试！', 'danger')
            print(f"Registration error: {str(e)}")
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/captcha')
def captcha():
    text, image = get_captcha_code_and_content()
    session['captcha'] = text
    return send_file(
        image,
        mimetype='image/png'
    )

@app.route('/students')
@login_required
@cache.cached(timeout=60, query_string=True)
def students():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 基础查询
    query = Student.query
    
    class_id = request.args.get('class_id')
    if class_id:
        query = query.filter(Student.class_id == class_id)
    elif current_user.role == 'teacher':
        # 获取教师负责的班级ID列表
        teacher_classes = Class.query.filter(Class.teacher_id == current_user.id).with_entities(Class.id).all()
        class_ids = [c.id for c in teacher_classes]
        if class_ids:
            query = query.filter(Student.class_id.in_(class_ids))
        else:
            # 如果教师没有负责的班级，显示空列表
            query = query.filter(Student.id == None)
    elif current_user.role == 'student':
        # 学生只能看到自己的信息
        query = query.filter(Student.user_id == current_user.id)
    
    # 执行分页查询
    students = query.order_by(Student.student_id).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('students.html', students=students)


@app.route('/student/create', methods=['GET', 'POST'])
@login_required
def create_student():
    if request.method == 'POST':
        try:
            # 获取表单数据
            student_id = request.form.get('student_id')
            class_id = request.form.get('class_id')
            name = request.form.get('name')

            # 检查学号是否已存在
            if Student.query.filter_by(student_id=student_id).first():
                flash('学号已存在！', 'danger')
                return redirect(url_for('create_student'))
                # 只创建学生记录，不创建用户账号
            student = Student(
                user_id=None,  # 初始时不关联用户账号
                student_id=student_id,
                name=name,
                gender=request.form.get('gender'),
                age=int(request.form.get('age')),
                class_id=class_id,
                status=StudentStatus.ACTIVE.value,
                admission_date=datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                address=request.form.get('address')
            )
            db.session.add(student)
            db.session.commit()
            flash('学生信息添加成功！学生可使用学号进行注册。', 'success')
            return redirect(url_for('students'))

        except Exception as e:
            db.session.rollback()
            flash(f'创建失败：{str(e)}', 'danger')
            print(f"Error creating student: {str(e)}")

    # GET请求处理
    departments = Department.query.all()
    return render_template('create_student.html', departments=departments)


@app.route('/student/<int:id>')
@login_required
def student_detail(id):
    student = Student.query.get_or_404(id)
    # 获取最近的状态变更记录
    status_changes = StudentStatusChange.query.filter_by(student_id=id).order_by(StudentStatusChange.created_at.desc()).all()
    return render_template('student_detail.html', student=student, status_changes=status_changes)

@app.route('/student/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@check_student_owner
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        try:
            # 管理员/教师可以编辑所有信息
            if current_user.role in ['admin', 'teacher']:
                student.gender = request.form.get('gender')
                student.age = int(request.form.get('age'))
            
            # 所有用户（包括学生）都可以编辑联系信息
            student.phone = request.form.get('phone')
            student.email = request.form.get('email')
            student.address = request.form.get('address')
            
            db.session.commit()
            flash('信息更新成功！', 'success')
              # 保持在学生详情页面
            return redirect(url_for('student_detail', id=id))
                
        except ValueError:
            db.session.rollback()
            flash('请输入有效的数据！', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
            
    return render_template('edit_student.html', student=student)

@app.route('/student/<int:id>/delete')
@login_required
def delete_student(id):
    try:
        student = Student.query.get_or_404(id)
        # 如果存在关联的用户账号，一并删除
        if student.user:
            user = User.query.get(student.user_id)
            if user:
                db.session.delete(user)
        db.session.delete(student)
        db.session.commit()
        flash('学生信息已删除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    return redirect(url_for('students'))

# 院系管理
@app.route('/departments')
@admin_required
@cache.cached(timeout=300)
def departments():
    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@app.route('/department/create', methods=['GET', 'POST'])
@admin_required
def create_department():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if Department.query.filter_by(name=name).first():
            app.logger.warning(f'创建院系失败: {name} 已存在')
            flash('院系已存在！', 'danger')
        else:
            department = Department(name=name, description=description)
            db.session.add(department)
            db.session.commit()
            app.logger.info(f'创建院系成功: {name}')
            flash('院系创建成功！', 'success')
            return redirect(url_for('departments'))
    return render_template('create_department.html')

@app.route('/department/delete/<int:id>')
@admin_required
def delete_department(id):
    try:
        department = Department.query.get_or_404(id)
        if department.majors:
            flash('该院系下还有专业，无法删除！', 'danger')
            return redirect(url_for('departments'))
        db.session.delete(department)
        db.session.commit()
        flash('院系删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    return redirect(url_for('departments'))

# 专业管理
@app.route('/majors')
@admin_required
def majors():
    majors = Major.query.all()
    return render_template('majors.html', majors=majors)

@app.route('/major/create', methods=['GET', 'POST'])
@admin_required
def create_major():
    if request.method == 'POST':
        name = request.form.get('name')
        department_id = request.form.get('department_id')
        description = request.form.get('description')
        
        major = Major(
            name=name,
            department_id=department_id,
            description=description
        )
        db.session.add(major)
        db.session.commit()
        flash('专业创建成功！', 'success')
        return redirect(url_for('majors'))
    departments = Department.query.all()
    return render_template('create_major.html', departments=departments)

@app.route('/major/delete/<int:id>')
@admin_required
def delete_major(id):
    try:
        major = Major.query.get_or_404(id)
        if major.classes:
            flash('该专业下还有班级，无法删除！', 'danger')
            return redirect(url_for('majors'))
        db.session.delete(major)
        db.session.commit()
        flash('专业删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    return redirect(url_for('majors'))

# 班级管理
@app.route('/classes')
@teacher_required
def classes():
    if current_user.role == 'admin':
        classes = Class.query.all()
    else:
        classes = Class.query.filter(Class.teacher_id == current_user.id).all()
    return render_template('classes.html', classes=classes)

@app.route('/class/create', methods=['GET', 'POST'])
@admin_required
def create_class():
    if request.method == 'POST':
        try:
            grade_id = request.form.get('grade_id')
            major_id = request.form.get('major_id')
            class_no = request.form.get('class_no')
            teacher_id = request.form.get('teacher_id') or None
            
            if not all([grade_id, major_id, class_no]):
                flash('请填写完整信息！', 'danger')
                return redirect(url_for('create_class'))
            
            grade = Grade.query.get(grade_id)
            major = Major.query.get(major_id)
            
            if not grade or not major:
                flash('年级或专业信息无效！', 'danger')
                return redirect(url_for('create_class'))
            
            # 生成班级名称：年级+专业+班号+班，如"2023软件01班"
            class_no = str(int(class_no)).zfill(2)  # 确保班号是两位数
            grade_year = grade.name.replace('级', '')  # 移除"级"字
            name = f"{grade_year}{major.name}{class_no}班"
            
            # 检查班级名称是否已存在
            if Class.query.filter_by(name=name).first():
                flash('该班级已存在！', 'danger')
                return redirect(url_for('create_class'))
            
            class_ = Class(
                name=name,
                grade_id=grade_id,
                major_id=major_id,
                teacher_id=teacher_id
            )
            db.session.add(class_)
            db.session.commit()
            flash('班级创建成功！', 'success')
            return redirect(url_for('classes'))
        except Exception as e:
            db.session.rollback()
            flash(f'创建班级失败：{str(e)}', 'danger')
            return redirect(url_for('create_class'))
        
    grades = Grade.query.all()
    majors = Major.query.all()
    teachers = User.query.filter(User.role == 'teacher').all()
    return render_template('create_class.html', grades=grades, majors=majors, teachers=teachers)

@app.route('/class/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_class(id):
    class_ = Class.query.get_or_404(id)
    if request.method == 'POST':
        try:
            grade_id = request.form.get('grade_id')
            major_id = request.form.get('major_id')
            class_no = request.form.get('class_no')
            teacher_id = request.form.get('teacher_id') or None
            
            if not all([grade_id, major_id, class_no]):
                flash('请填写完整信息！', 'danger')
                return redirect(url_for('edit_class', id=id))
            
            grade = Grade.query.get(grade_id)
            major = Major.query.get(major_id)
            
            if not grade or not major:
                flash('年级或专业信息无效！', 'danger')
                return redirect(url_for('edit_class', id=id))
            
            # 生成新的班级名称
            class_no = str(int(class_no)).zfill(2)  # 确保班号是两位数
            grade_year = grade.name.replace('级', '')  # 移除"级"字
            new_name = f"{grade_year}{major.name}{class_no}班"
            
            # 检查新班级名称是否已存在（排除当前班级）
            existing_class = Class.query.filter(Class.name == new_name, Class.id != id).first()
            if existing_class:
                flash('该班级名称已存在！', 'danger')
                return redirect(url_for('edit_class', id=id))
            
            class_.name = new_name
            class_.grade_id = grade_id
            class_.major_id = major_id
            class_.teacher_id = teacher_id
            
            db.session.commit()
            flash('班级信息更新成功！', 'success')
            return redirect(url_for('classes'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
            
    grades = Grade.query.all()
    majors = Major.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('edit_class.html', 
                         class_=class_, 
                         grades=grades,
                         majors=majors,
                         teachers=teachers)

@app.route('/class/delete/<int:id>')
@admin_required
def delete_class(id):
    try:
        class_ = Class.query.get_or_404(id)
        if class_.students:
            flash('该班级下还有学生，无法删除！', 'danger')
            return redirect(url_for('classes'))
        db.session.delete(class_)
        db.session.commit()
        flash('班级删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    return redirect(url_for('classes'))

# 学籍异动
@app.route('/student/<int:id>/status', methods=['GET', 'POST'])
@teacher_required
def change_student_status(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        new_status = request.form.get('status')
        reason = request.form.get('reason')
        effective_date = datetime.strptime(request.form.get('effective_date'), '%Y-%m-%d')
        
        status_change = StudentStatusChange(
            student_id=student.id,
            old_status=student.status,
            new_status=new_status,
            change_reason=reason,
            effective_date=effective_date,
            created_by=current_user.id
        )
        
        student.status = new_status
        if new_status in [StudentStatus.GRADUATED.value, StudentStatus.COMPLETED.value]:
            student.graduation_date = effective_date

        db.session.add(status_change)
        db.session.commit()

        # 异步发送状态变更通知
        send_status_change_notification.delay(
            student_id=student.id,
            old_status=status_change.old_status,
            new_status=new_status,
            reason=reason
        )

        flash('学籍状态更新成功！已异步发送通知。', 'success')
        return redirect(url_for('student_detail', id=id))
    return render_template('change_student_status.html', student=student, statuses=StudentStatus)

# 转专业申请
@app.route('/student/<int:id>/apply_transfer', methods=['GET', 'POST'])
@login_required
def apply_transfer(id):
    student = Student.query.get_or_404(id)
    # 检查是否是本人操作
    if current_user.role == 'student' and student.user_id != current_user.id:
        abort(403)
    # 检查是否有待处理的申请
    if MajorTransfer.query.filter_by(student_id=id, status='待审核').first():
        flash('您已有待处理的转专业申请！', 'warning')
        return redirect(url_for('student_detail', id=id))
    
    if request.method == 'POST':
        major_id = request.form.get('major_id')
        reason = request.form.get('reason')
        contact_phone = request.form.get('contact_phone')
        
        transfer = MajorTransfer(
            student_id=student.id,
            old_class_id=student.class_id,
            new_major_id=major_id,
            transfer_reason=reason,
            contact_phone=contact_phone,
            status='待审核'
        )
        
        db.session.add(transfer)
        db.session.commit()
        flash('转专业申请已提交，请等待审核！', 'success')
        return redirect(url_for('student_detail', id=id))
        
    majors = Major.query.all()
    return render_template('apply_transfer.html', student=student, majors=majors)

# 转专业申请审核列表
@app.route('/transfers/review')
@teacher_required
def review_transfers():
    if current_user.role == 'admin':
        transfers = MajorTransfer.query.order_by(MajorTransfer.created_at.desc()).all()
    else:
        # 教师只能看到自己班级学生的申请
        teacher_class_ids = [c.id for c in Class.query.filter_by(teacher_id=current_user.id).all()]
        transfers = MajorTransfer.query.filter(
            MajorTransfer.old_class_id.in_(teacher_class_ids)
        ).order_by(MajorTransfer.created_at.desc()).all()
    
    return render_template('review_transfers.html', transfers=transfers)

# 处理转专业申请
@app.route('/transfer/<int:id>/<action>')
@teacher_required
def process_transfer(id, action):
    transfer = MajorTransfer.query.get_or_404(id)
    
    # 只有管理员或原班级的教师可以处理
    if current_user.role != 'admin':
        class_ = Class.query.get(transfer.old_class_id)
        if class_.teacher_id != current_user.id:
            abort(403)
    
    if action == 'approve':
        # 查找目标专业的班级
        target_class = Class.query.filter_by(
            major_id=transfer.new_major_id,
            grade_id=transfer.old_class.grade_id
        ).first()

        if not target_class:
            flash('目标专业没有对应年级的班级！', 'danger')
            return redirect(url_for('review_transfers'))

        transfer.status = '已通过'
        transfer.new_class_id = target_class.id
        transfer.approved_by = current_user.id
        transfer.approved_at = datetime.utcnow()

        # 更新学生班级
        student = Student.query.get(transfer.student_id)
        student.class_id = target_class.id

    elif action == 'reject':
        transfer.status = '已拒绝'
        transfer.approved_by = current_user.id
        transfer.approved_at = datetime.utcnow()

    db.session.commit()

    # 异步发送审批结果通知
    send_transfer_result_notification.delay(
        transfer_id=transfer.id,
        action=action
    )

    flash(f'转专业申请已{transfer.status}！已异步发送通知。', 'success')
    return redirect(url_for('review_transfers'))

# 学籍异动记录查询
@app.route('/student/<int:id>/status_history')
@login_required
def student_status_history(id):
    student = Student.query.get_or_404(id)
    if current_user.role == 'student' and current_user.id != student.user_id:
        abort(403)
    status_changes = StudentStatusChange.query.filter_by(student_id=id).order_by(StudentStatusChange.created_at.desc()).all()
    transfers = MajorTransfer.query.filter_by(student_id=id).order_by(MajorTransfer.created_at.desc()).all()
    return render_template('student_status_history.html', student=student, status_changes=status_changes, transfers=transfers)

# 教师账户管理
@app.route('/teachers')
@admin_required
def teachers():
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/teacher/create', methods=['GET', 'POST'])
@admin_required
def create_teacher():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        real_name = request.form.get('real_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'danger')
            return redirect(url_for('create_teacher'))
            
        new_teacher = User(
            username=username,
            password=password,  # 明文存储密码
            real_name=real_name,
            role='teacher',
            phone=phone,
            email=email
        )
        db.session.add(new_teacher)
        try:
            db.session.commit()
            flash('教师账户创建成功！', 'success')
            return redirect(url_for('teachers'))
        except:
            db.session.rollback()
            flash('创建失败，请重试！', 'danger')
    return render_template('create_teacher.html')

@app.route('/teacher/delete/<int:id>')
@admin_required
def delete_teacher(id):
    try:
        teacher = User.query.get_or_404(id)
        if teacher.teacher_classes or teacher.counselor_classes:
            flash('该教师还有关联的班级，无法删除！', 'danger')
            return redirect(url_for('teachers'))
        db.session.delete(teacher)
        db.session.commit()
        flash('教师账户删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    return redirect(url_for('teachers'))

# 年级管理
@app.route('/grades')
@admin_required
def grades():
    grades = Grade.query.order_by(Grade.year.desc()).all()
    return render_template('grades.html', grades=grades)

@app.route('/grade/create', methods=['GET', 'POST'])
@admin_required
def create_grade():
    if request.method == 'POST':
        try:
            year = int(request.form.get('year', '0'))
            name = request.form.get('name', '').strip()
            
            if not year or not name:
                flash('请填写完整的年级信息！', 'danger')
                return redirect(url_for('create_grade'))
                
            if Grade.query.filter_by(year=year, name=name).first():
                flash('该年级已存在！', 'danger')
                return redirect(url_for('create_grade'))
                
            grade = Grade(
                year=year,
                name=name
            )
            db.session.add(grade)
            db.session.commit()
            flash('年级创建成功！', 'success')
            return redirect(url_for('grades'))
        except ValueError:
            flash('年份必须是有效的数字！', 'danger')
            return redirect(url_for('create_grade'))
        except Exception as e:
            db.session.rollback()
            flash(f'创建失败：{str(e)}', 'danger')
            return redirect(url_for('create_grade'))
            
    return render_template('create_grade.html')

@app.route('/api/majors')
@login_required
def get_majors():
    try:
        department_id = request.args.get('department_id')
        if not department_id:
            return jsonify({'error': 'Missing department_id parameter'}), 400
        
        majors = Major.query.filter_by(department_id=department_id).all()
        print(f"Debug - Found {len(majors)} majors for department_id {department_id}")
        return jsonify([{
            'id': major.id,
            'name': major.name
        } for major in majors])
    except Exception as e:
        print(f"Error in get_majors: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classes')
@login_required
def get_classes():
    try:
        major_id = request.args.get('major_id')
        if not major_id:
            return jsonify({'error': 'Missing major_id parameter'}), 400
        
        classes = Class.query.filter_by(major_id=major_id).all()
        print(f"Debug - Found {len(classes)} classes for major_id {major_id}")
        return jsonify([{
            'id': class_.id,
            'name': class_.name
        } for class_ in classes])
    except Exception as e:
        print(f"Error in get_classes: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 批量导入学生（异步任务）
@app.route('/student/batch_import', methods=['POST'])
@admin_required
def batch_import():
    """提交批量导入任务"""
    try:
        import json
        students_data = request.json.get('students', [])

        if not students_data:
            return jsonify({'status': 'error', 'message': '没有数据'}), 400

        # 提交异步任务
        task = batch_import_students.delay(students_data)

        return jsonify({
            'status': 'success',
            'message': '批量导入任务已提交',
            'task_id': task.id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/task/<task_id>/status')
@login_required
def task_status(task_id):
    """查询异步任务状态"""
    from celery.result import AsyncResult
    task = AsyncResult(task_id, app=celery)

    response = {
        'task_id': task_id,
        'status': task.status,
        'result': task.result if task.ready() else None
    }
    return jsonify(response)


# 生成学籍报告（异步任务）
@app.route('/student/<int:id>/generate_report')
@login_required
def generate_report(id):
    """提交生成学籍报告任务"""
    student = Student.query.get_or_404(id)

    # 权限检查
    if current_user.role == 'student' and student.user_id != current_user.id:
        abort(403)

    # 提交异步任务
    task = send_grade_report.delay(id)

    flash('学籍报告生成任务已提交，请稍后查看。', 'info')
    return redirect(url_for('student_detail', id=id))


# 批量导入页面
@app.route('/student/batch_import/page')
@admin_required
def batch_import_page():
    """批量导入学生页面"""
    return render_template('batch_import.html')


if __name__ == '__main__':
    app.run(debug=True)
