#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온누리인쇄나라 강화된 웹사이트 - 기존 프로그램 연동
기존 마케팅 시스템, AI 디자인, 블로그 포스팅 시스템과 연동
"""

import os
import sys
import json
import hashlib
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
import threading
import time
import uuid
import subprocess
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Circle, String
from reportlab.graphics import renderPDF
import io

# 기존 프로그램들 import
try:
    from working_print_shop_marketing import WorkingPrintShopMarketing
    MARKETING_AVAILABLE = True
except ImportError:
    MARKETING_AVAILABLE = False
    print("⚠️ 마케팅 시스템을 찾을 수 없습니다.")

try:
    from ai_cover_designer import AICoverDesigner
    AI_DESIGN_AVAILABLE = True
except ImportError:
    AI_DESIGN_AVAILABLE = False
    print("⚠️ AI 디자인 시스템을 찾을 수 없습니다.")

try:
    from naver_blog_auto_poster import NaverBlogContentGenerator
    BLOG_AVAILABLE = True
except ImportError:
    BLOG_AVAILABLE = False
    print("⚠️ 블로그 포스팅 시스템을 찾을 수 없습니다.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'onnuri-print-enhanced-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///onnuri_print_enhanced.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

# 이메일 설정 (네이버 메일)
app.config['MAIL_SERVER'] = 'smtp.naver.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'print7123@naver.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'  # 실제 앱 비밀번호로 변경 필요

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 기존 프로그램 인스턴스 초기화
marketing_system = None
ai_designer = None
blog_generator = None

if MARKETING_AVAILABLE:
    try:
        marketing_system = WorkingPrintShopMarketing()
        print("✅ 마케팅 시스템 연동 완료")
    except Exception as e:
        print(f"❌ 마케팅 시스템 연동 실패: {e}")

if AI_DESIGN_AVAILABLE:
    try:
        ai_designer = AICoverDesigner()
        print("✅ AI 디자인 시스템 연동 완료")
    except Exception as e:
        print(f"❌ AI 디자인 시스템 연동 실패: {e}")

if BLOG_AVAILABLE:
    try:
        blog_generator = NaverBlogContentGenerator()
        print("✅ 블로그 포스팅 시스템 연동 완료")
    except Exception as e:
        print(f"❌ 블로그 포스팅 시스템 연동 실패: {e}")

# 데이터베이스 모델 (기존 + 확장)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True)
    questions = db.relationship('Question', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
    # 인쇄 설정
    print_type = db.Column(db.String(20), nullable=False)
    binding_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(50), nullable=False)
    
    # 견적 정보
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # 파일 정보
    file_path = db.Column(db.String(500))
    special_requirements = db.Column(db.Text)
    
    # 주문 상태
    status = db.Column(db.String(20), default='견적요청')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    is_answered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)

# 새로운 모델들
class MarketingLead(db.Model):
    """마케팅 리드 관리"""
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    search_count = db.Column(db.Integer, default=1)
    first_detected = db.Column(db.DateTime, default=datetime.utcnow)
    last_detected = db.Column(db.DateTime, default=datetime.utcnow)
    converted = db.Column(db.Boolean, default=False)
    converted_at = db.Column(db.DateTime)

class AIDesignRequest(db.Model):
    """AI 디자인 요청 관리"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    design_style = db.Column(db.String(50), nullable=False)
    custom_description = db.Column(db.Text)
    status = db.Column(db.String(20), default='요청중')
    generated_image_path = db.Column(db.String(500))
    final_pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    """블로그 포스트 관리"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='초안')
    posted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_order_number():
    return f"ONN{datetime.now().strftime('%Y%m%d%H%M%S')}"

def calculate_price(print_type, binding_type, quantity, pages, size, print_method='single'):
    """정확한 단가표 기반 견적 계산 로직 - 고정된 가격표 (2025.01.02 기준)"""
    
    # 페이지 수에 따른 출력 가격 계산
    def get_print_price(print_type, pages, print_method):
        # 페이지 수 구간별 가격표 - 2025.01.02 공식 가격표 고정
        if pages <= 500:
            price_ranges = {
                'black_white': {'single': 40, 'double': 40},  # 고정: 레이져흑백 500P이하
                'laser_color': {'single': 150, 'double': 150},  # 고정: 레이져칼라 500P이하
                'ink_color': {'single': 70, 'double': 70}  # 고정: 잉크칼라 500P이하
            }
        elif pages <= 5000:
            price_ranges = {
                'black_white': {'single': 38, 'double': 33},  # 고정: 레이져흑백 501-5,000P
                'laser_color': {'single': 115, 'double': 110},  # 고정: 레이져칼라 501-5,000P
                'ink_color': {'single': 66, 'double': 60}  # 고정: 잉크칼라 501-5,000P
            }
        elif pages <= 10000:
            price_ranges = {
                'black_white': {'single': 30, 'double': 25},  # 고정: 레이져흑백 5,001-10,000P
                'laser_color': {'single': 93, 'double': 88},  # 고정: 레이져칼라 5,001-10,000P
                'ink_color': {'single': 55, 'double': 50}  # 고정: 잉크칼라 5,001-10,000P
            }
        elif pages <= 15000:
            price_ranges = {
                'black_white': {'single': 27, 'double': 22},  # 고정: 레이져흑백 10,001-15,000P
                'laser_color': {'single': 82, 'double': 77},  # 고정: 레이져칼라 10,001-15,000P
                'ink_color': {'single': 50, 'double': 45}  # 고정: 잉크칼라 10,001-15,000P
            }
        else:  # 15001페이지 이상
            price_ranges = {
                'black_white': {'single': 25, 'double': 20},  # 고정: 레이져흑백 15,001P이상
                'laser_color': {'single': 72, 'double': 66},  # 고정: 레이져칼라 15,001P이상
                'ink_color': {'single': 45, 'double': 40}  # 고정: 잉크칼라 15,001P이상
            }
        
        return price_ranges.get(print_type, {'single': 40, 'double': 40})[print_method]
    
    # 수량에 따른 제본 가격 계산 - 2025.01.02 공식 가격표 고정
    def get_binding_price(binding_type, quantity):
        if binding_type == 'ring':
            if quantity <= 30:
                return 2200  # 고정: 링제본 1-30부
            elif quantity <= 49:
                return 1650  # 고정: 링제본 31-49부
            elif quantity <= 99:
                return 1430  # 고정: 링제본 50-99부
            else:  # 100부 이상
                return 1100  # 고정: 링제본 100부이상
        elif binding_type == 'perfect':
            if quantity <= 30:
                return 2200  # 고정: 무선제본 1-30부
            elif quantity <= 49:
                return 1100  # 고정: 무선제본 31-49부
            elif quantity <= 99:
                return 770   # 고정: 무선제본 50-99부
            else:  # 100부 이상
                return 770   # 고정: 무선제본 100부이상
        elif binding_type == 'saddle':
            return 330  # 고정: 중철제본 부당 330원
        elif binding_type == 'folding':
            return 500  # 고정: 접지제본 기본 가격
        else:
            return 0
    
    # 총 페이지 수 계산 (페이지 × 수량)
    total_pages = pages * quantity
    
    # 출력 가격 계산 (총 페이지 수 기준)
    unit_print_price = get_print_price(print_type, total_pages, print_method)
    total_print_price = unit_print_price * total_pages
    
    # 제본 가격 계산 (부당 가격)
    unit_binding_price = get_binding_price(binding_type, quantity)
    total_binding_price = unit_binding_price * quantity
    
    # 총 가격 (출력비 + 제본비) - 부가세 포함
    total_price_with_tax = total_print_price + total_binding_price
    
    # 세액 계산 (부가세 10%)
    tax_amount = round(total_price_with_tax * 0.1)
    
    # 총 가격 (부가세 제외) - 합계금액에서 세액 제외
    total_price_without_tax = total_price_with_tax - tax_amount
    
    # 단위 가격 (페이지당 출력 비용 + 제본 비용) - 상수 기반 계산
    unit_price = (unit_print_price * pages) + unit_binding_price
    
    return {
        'unit_price': unit_price,
        'total_price': total_price_without_tax,  # 부가세 제외된 금액
        'total_price_with_tax': total_price_with_tax,  # 부가세 포함된 금액
        'tax_amount': tax_amount,
        'discount_rate': 0,  # 할인은 제본 가격에 이미 반영됨
        'print_price': total_print_price,
        'binding_price': total_binding_price,
        'unit_print_price': unit_print_price,
        'unit_binding_price': unit_binding_price,
        'pages': pages,
        'total_pages': total_pages
    }

# 라우트들
@app.route('/')
def index():
    """강화된 메인 페이지"""
    # 마케팅 통계 가져오기
    marketing_stats = get_marketing_stats()
    
    # 최근 작업 사례 가져오기
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(6).all()
    
    return render_template('index.html', 
                         marketing_stats=marketing_stats,
                         recent_orders=recent_orders)

@app.route('/quote', methods=['GET', 'POST'])
def quote():
    """강화된 견적 계산"""
    if request.method == 'POST':
        try:
            data = request.get_json()
        
            # 필수 데이터 검증
            if not data:
                return jsonify({'error': '견적 데이터가 없습니다.'}), 400
            
            required_fields = ['printType', 'bindingType', 'quantity', 'pages']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
            
            # 견적 계산
            price_info = calculate_price(
                data['printType'],
                data['bindingType'],
                safe_int_conversion(data['quantity']),
                safe_int_conversion(data['pages']),
                data.get('size', 'A4'),
                data.get('printMethod', 'single')
            )
            
            # 마케팅 리드 생성
            try:
                create_marketing_lead(data)
            except Exception as e:
                print(f"마케팅 리드 생성 오류: {e}")
        
            # 이메일 견적서 전송 (이메일이 제공된 경우)
            if data.get('email'):
                try:
                    send_quote_email(data, price_info)
                except Exception as e:
                    print(f"이메일 전송 오류: {e}")
            
            return jsonify(price_info)
            
        except Exception as e:
            print(f"견적 계산 오류: {e}")
            return jsonify({'error': f'견적 계산 중 오류가 발생했습니다: {str(e)}'}), 500
    
    return render_template('quote.html')

@app.route('/ai-design', methods=['GET', 'POST'])
@login_required
def ai_design():
    """AI 디자인 서비스"""
    if request.method == 'POST':
        title = request.form['title']
        company_name = request.form['company_name']
        design_style = request.form['design_style']
        custom_description = request.form.get('custom_description', '')
        
        # AI 디자인 요청 생성
        design_request = AIDesignRequest(
            user_id=current_user.id,
            title=title,
            company_name=company_name,
            design_style=design_style,
            custom_description=custom_description
        )
        
        db.session.add(design_request)
        db.session.commit()
        
        # AI 디자인 생성 (백그라운드)
        if ai_designer:
            threading.Thread(target=generate_ai_design, args=(design_request.id,)).start()
        
        flash('AI 디자인 요청이 접수되었습니다. 잠시만 기다려주세요.', 'success')
        return redirect(url_for('ai_design_status', request_id=design_request.id))
    
    return render_template('ai_design.html')

@app.route('/ai-design/status/<int:request_id>')
@login_required
def ai_design_status(request_id):
    """AI 디자인 상태 확인"""
    design_request = AIDesignRequest.query.get_or_404(request_id)
    if design_request.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('ai_design'))
    
    return render_template('ai_design_status.html', design_request=design_request)

@app.route('/marketing-dashboard')
@login_required
def marketing_dashboard():
    """마케팅 대시보드"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    # 마케팅 통계
    stats = get_marketing_stats()
    
    # 최근 리드
    recent_leads = MarketingLead.query.order_by(MarketingLead.last_detected.desc()).limit(20).all()
    
    # 블로그 포스트 현황
    blog_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(10).all()
    
    return render_template('marketing_dashboard.html',
                         stats=stats,
                         recent_leads=recent_leads,
                         blog_posts=blog_posts)

@app.route('/blog-management')
@login_required
def blog_management():
    """블로그 관리"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog_management.html', posts=posts)

@app.route('/blog/create-post', methods=['GET', 'POST'])
@login_required
def create_blog_post():
    """블로그 포스트 생성"""
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        topic = request.form['topic']
        keyword = request.form['keyword']
        content = request.form['content']
        
        # 블로그 포스트 생성
        post = BlogPost(
            title=title,
            content=content,
            topic=topic,
            keyword=keyword,
            status='초안'
        )
        
        db.session.add(post)
        db.session.commit()
        
        # 블로그에 자동 포스팅 (백그라운드)
        if blog_generator:
            threading.Thread(target=post_to_blog, args=(post.id,)).start()
        
        flash('블로그 포스트가 생성되었습니다.', 'success')
        return redirect(url_for('blog_management'))
    
    return render_template('create_blog_post.html')

# 유틸리티 함수들
def get_marketing_stats():
    """마케팅 통계 가져오기"""
    if not marketing_system:
        return {}
    
    try:
        # 마케팅 시스템에서 통계 가져오기
        stats = {
            'total_leads': MarketingLead.query.count(),
            'converted_leads': MarketingLead.query.filter_by(converted=True).count(),
            'top_keywords': db.session.query(MarketingLead.keyword, db.func.count(MarketingLead.id)).group_by(MarketingLead.keyword).order_by(db.func.count(MarketingLead.id).desc()).limit(5).all(),
            'recent_leads': MarketingLead.query.order_by(MarketingLead.last_detected.desc()).limit(5).all()
        }
        return stats
    except Exception as e:
        print(f"마케팅 통계 가져오기 실패: {e}")
        return {}

def create_marketing_lead(data):
    """마케팅 리드 생성"""
    try:
        # 키워드 추출
        keyword = extract_keyword_from_data(data)
        if keyword:
            # 기존 리드 확인
            existing_lead = MarketingLead.query.filter_by(keyword=keyword).first()
            if existing_lead:
                existing_lead.search_count += 1
                existing_lead.last_detected = datetime.utcnow()
            else:
                new_lead = MarketingLead(
                    keyword=keyword,
                    category='quote_request',
                    search_count=1
                )
                db.session.add(new_lead)
            
            db.session.commit()
    except Exception as e:
        print(f"마케팅 리드 생성 실패: {e}")

def send_quote_email(data, price_info):
    """견적서를 이메일로 전송 (직인 포함)"""
    try:
        customer_name = data.get('customerName', '고객님')
        email = data.get('email')
        pages = data.get('pages')
        print_type = data.get('printType')
        binding_type = data.get('bindingType')
        quantity = data.get('quantity')
        
        # 출력 타입 한글 변환
        print_type_map = {
            'black_white': '레이저흑백',
            'laser_color': '레이저칼라',
            'ink_color': '잉크칼라'
        }
        
        # 제본 타입 한글 변환
        binding_type_map = {
            'ring': '링제본',
            'perfect': '무선제본',
            'saddle': '중철제본',
            'folding': '접지'
        }
        
        # 이메일 제목
        subject = f"[온누리인쇄나라] 견적서 - {customer_name}님"
        
        # HTML 이메일 내용 (직인 포함)
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>견적서</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007ACC;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .company-name {{
            font-size: 28px;
            font-weight: bold;
            color: #007ACC;
            margin-bottom: 10px;
        }}
        .quote-title {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .quote-info {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .price-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .price-table th, .price-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .price-table th {{
            background-color: #007ACC;
            color: white;
            font-weight: bold;
        }}
        .total-price {{
            font-size: 20px;
            font-weight: bold;
            color: #007ACC;
            text-align: right;
        }}
        .contact-info {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .stamp-section {{
            text-align: right;
            margin-top: 40px;
            position: relative;
        }}
        .stamp {{
            display: inline-block;
            width: 120px;
            height: 120px;
            border: 3px solid #dc3545;
            border-radius: 50%;
            position: relative;
            background: linear-gradient(45deg, #fff, #f8f9fa);
        }}
        .stamp-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 14px;
            font-weight: bold;
            color: #dc3545;
            text-align: center;
            line-height: 1.2;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">온누리인쇄나라</div>
        <div class="quote-title">견적서</div>
    </div>
    
    <div class="quote-info">
        <p><strong>고객명:</strong> {customer_name}</p>
        <p><strong>견적일:</strong> 2025년 08월 11일</p>
    </div>
    
    <h3>📋 인쇄 사양</h3>
    <table class="price-table">
        <tr>
            <th>항목</th>
            <th>내용</th>
        </tr>
        <tr>
            <td>페이지 수</td>
            <td>{pages}페이지</td>
        </tr>
        <tr>
            <td>출력 타입</td>
            <td>{print_type_map.get(print_type, print_type)}</td>
        </tr>
        <tr>
            <td>제본 방식</td>
            <td>{binding_type_map.get(binding_type, binding_type)}</td>
        </tr>
        <tr>
            <td>수량</td>
            <td>{quantity}권</td>
        </tr>
    </table>
    
    <h3>💰 가격 내역</h3>
    <table class="price-table">
        <tr>
            <th>항목</th>
            <th>금액</th>
        </tr>
        <tr>
            <td>페이지당 단가</td>
            <td>{price_info['unit_print_price']:,}원</td>
        </tr>
        <tr>
            <td>총 출력 가격</td>
            <td>{price_info['print_price']:,}원</td>
        </tr>
        <tr>
            <td>제본 가격</td>
            <td>{price_info['binding_price']:,}원</td>
        </tr>
        <tr>
            <td>단가 (출력+제본)</td>
            <td>{price_info['unit_price']:,}원</td>
        </tr>
        <tr style="background-color: #e3f2fd;">
            <td><strong>총 가격</strong></td>
            <td class="total-price"><strong>{price_info['total_price']:,}원</strong></td>
        </tr>
    </table>
    
    <div class="contact-info">
        <h4>📞 문의 및 주문</h4>
        <p><strong>전화:</strong> 02-6338-7123</p>
        <p><strong>휴대폰:</strong> 010-2624-7123</p>
        <p><strong>이메일:</strong> print7123@naver.com</p>
        <p><strong>웹사이트:</strong> https://print7123.com/</p>
        <p><strong>영업시간:</strong> 09:30-16:00 (월-금)</p>
    </div>
    
    <div class="stamp-section">
        <div class="stamp">
            <div class="stamp-text">
                온누리인쇄나라<br>
                대표: 김인쇄<br>
                {datetime.now().strftime('%Y.%m.%d')}
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>※ 안내사항</strong></p>
        <ul>
            <li>기본 80g 복사용지, 부가세 포함</li>
            <li>페이지 수와 수량에 따른 차등 가격 적용</li>
            <li>본 견적서는 7일간 유효합니다</li>
            <li>실제 가격은 최종 확인 후 결정됩니다</li>
        </ul>
        <p style="text-align: center; margin-top: 20px;">
            <strong>감사합니다. 온누리인쇄나라 드림</strong>
        </p>
    </div>
</body>
</html>
        """
        
        # 텍스트 버전 (HTML을 지원하지 않는 이메일 클라이언트용)
        text_content = f"""
안녕하세요, {customer_name}님!

온누리인쇄나라에서 요청하신 견적서를 보내드립니다.

========================================
           견적서
========================================

고객명: {customer_name}
견적일: 2025년 08월 11일

[인쇄 사양]
페이지 수: {pages}페이지
출력 타입: {print_type_map.get(print_type, print_type)}
제본 방식: {binding_type_map.get(binding_type, binding_type)}
수량: {quantity}권

[가격 내역]
페이지당 단가: {price_info['unit_print_price']:,}원
총 출력 가격: {price_info['print_price']:,}원
제본 가격: {price_info['binding_price']:,}원
단가 (출력+제본): {price_info['unit_price']:,}원
총 가격: {price_info['total_price']:,}원

※ 기본 80g 복사용지, 부가세 포함
※ 페이지 수와 수량에 따른 차등 가격 적용

========================================

문의사항이나 주문을 원하시면 언제든 연락주세요!

📞 전화: 02-6338-7123
📱 휴대폰: 010-2624-7123
📧 이메일: print7123@naver.com
🌐 웹사이트: https://print7123.com/

⏰ 영업시간: 09:30-16:00 (월-금)

※ 본 견적서는 7일간 유효합니다.
※ 실제 가격은 최종 확인 후 결정됩니다.

감사합니다.
온누리인쇄나라 드림
        """
        
        # HTML 이메일 발송
        if send_html_email(email, subject, html_content, text_content):
            print(f"✅ 견적서 이메일 전송 성공: {email}")
            return True
        else:
            print(f"❌ 견적서 이메일 전송 실패: {email}")
            return False
            
    except Exception as e:
        print(f"견적서 이메일 전송 오류: {e}")
        return False

def send_html_email(to_email, subject, html_content, text_content):
    """HTML 이메일 발송"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 텍스트 버전
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTML 버전
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 이메일 발송
        context = ssl.create_default_context()
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls(context=context)
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"HTML 이메일 발송 오류: {e}")
        return False

def extract_keyword_from_data(data):
    """데이터에서 키워드 추출"""
    keywords = []
    
    # 인쇄 타입에서 키워드 추출
    print_type_map = {
        'black_white': '흑백인쇄',
        'ink_color': '잉크칼라인쇄',
        'laser_color': '레이저칼라인쇄'
    }
    
    binding_type_map = {
        'ring': '링제본',
        'perfect': '무선제본',
        'saddle': '중철제본',
        'folding': '접지제본'
    }
    
    if data.get('printType'):
        keywords.append(print_type_map.get(data['printType'], data['printType']))
    
    if data.get('bindingType'):
        keywords.append(binding_type_map.get(data['bindingType'], data['bindingType']))
    
    return ' '.join(keywords) if keywords else None

def generate_ai_design(request_id):
    """AI 디자인 생성 (백그라운드)"""
    try:
        design_request = AIDesignRequest.query.get(request_id)
        if not design_request or not ai_designer:
            return
        
        # AI 디자인 생성
        result = ai_designer.create_cover_design(
            title=design_request.title,
            company_name=design_request.company_name,
            design_style=design_request.design_style,
            custom_description=design_request.custom_description
        )
        
        if result.get('success'):
            design_request.status = '완료'
            design_request.generated_image_path = result.get('image_path')
            design_request.final_pdf_path = result.get('pdf_path')
        else:
            design_request.status = '실패'
        
        db.session.commit()
        
    except Exception as e:
        print(f"AI 디자인 생성 실패: {e}")
        design_request = AIDesignRequest.query.get(request_id)
        if design_request:
            design_request.status = '실패'
            db.session.commit()

def post_to_blog(post_id):
    """블로그에 포스팅 (백그라운드)"""
    try:
        post = BlogPost.query.get(post_id)
        if not post or not blog_generator:
            return
        
        # 블로그 포스팅
        success = blog_generator.post_to_blog({
            'title': post.title,
            'content': post.content,
            'topic': post.topic,
            'keyword': post.keyword
        })
        
        if success:
            post.status = '발행완료'
            post.posted_at = datetime.utcnow()
        else:
            post.status = '발행실패'
        
        db.session.commit()
        
    except Exception as e:
        print(f"블로그 포스팅 실패: {e}")
        post = BlogPost.query.get(post_id)
        if post:
            post.status = '발행실패'
            db.session.commit()

@app.route('/preview_quote', methods=['POST'])
def preview_quote():
    """견적서 미리보기 (텍스트 기반)"""
    try:
        data = request.get_json()
        
        # 필수 데이터 검증
        if not data:
            return jsonify({'error': '견적 데이터가 없습니다.'}), 400
        
        required_fields = ['printType', 'bindingType', 'quantity', 'pages']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
        
        # 견적 계산
        price_info = calculate_price(
            data['printType'],
            data['bindingType'],
            safe_int_conversion(data['quantity']),
            safe_int_conversion(data['pages']),
            data.get('size', 'A4'),
            data.get('printMethod', 'single')
        )
        
        # 텍스트 기반 미리보기 제공
        return jsonify({
            'success': True,
            'preview_image': None,
            'price_info': price_info,
            'fallback': True
        })
        
    except Exception as e:
        print(f"미리보기 생성 오류: {e}")
        return jsonify({'error': '미리보기 생성 중 오류가 발생했습니다.'}), 500

@app.route('/download_quote_pdf', methods=['POST'])
def download_quote_pdf():
    """견적서 PDF 다운로드"""
    try:
        data = request.get_json()
        
        # 필수 데이터 검증
        if not data:
            return jsonify({'error': '견적 데이터가 없습니다.'}), 400
        
        required_fields = ['printType', 'bindingType', 'quantity', 'pages']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
        
        # 견적 계산
        price_info = calculate_price(
            data['printType'],
            data['bindingType'],
            safe_int_conversion(data['quantity']),
            safe_int_conversion(data['pages']),
            data.get('size', 'A4'),
            data.get('printMethod', 'single')
        )
        
        # PDF 생성
        pdf_buffer = generate_quote_pdf(data, price_info)
        
        # 파일명 생성
        customer_name = data.get('customerName', '고객')
        filename = f"견적서_{customer_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"PDF 생성 오류: {e}")
        return jsonify({'error': 'PDF 생성 중 오류가 발생했습니다.'}), 500

# 기존 라우트들 유지
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('파일이 선택되지 않았습니다.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('파일이 선택되지 않았습니다.')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            flash('파일이 성공적으로 업로드되었습니다.')
            return redirect(url_for('my_orders'))
        else:
            flash('허용되지 않는 파일 형식입니다.')
    
    return render_template('upload.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 필수 항목만 강제, 선택 항목은 기본값 처리
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        if not username or not email or not password:
            flash('사용자명, 이메일, 비밀번호는 필수입니다.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자명입니다.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('이미 존재하는 이메일입니다.')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone or None,
            address=address or None
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('잘못된 사용자명 또는 비밀번호입니다.')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/go/official')
def go_official():
    """공식 사이트로 이동"""
    return redirect('https://print7123.com', code=302)

def register_korean_fonts():
    """한글 폰트 등록"""
    try:
        # Windows 시스템 폰트 경로
        font_paths = [
            'C:/Windows/Fonts/malgun.ttf',  # 맑은 고딕
            'C:/Windows/Fonts/malgunbd.ttf',  # 맑은 고딕 Bold
            'C:/Windows/Fonts/gulim.ttc',  # 굴림
            'C:/Windows/Fonts/batang.ttc',  # 바탕
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    if font_path.endswith('.ttf'):
                        pdfmetrics.registerFont(TTFont('Malgun', font_path))
                        pdfmetrics.registerFont(TTFont('MalgunBold', font_path))
                    elif font_path.endswith('.ttc'):
                        # TTC 파일의 경우 첫 번째 폰트만 등록
                        pdfmetrics.registerFont(TTFont('Malgun', font_path, subfontIndex=0))
                    print(f"✅ 폰트 등록 성공: {font_path}")
                    break
                except Exception as e:
                    print(f"⚠️ 폰트 등록 실패: {font_path} - {e}")
                    continue
        
        # 기본 폰트 설정
        return 'Malgun'
        
    except Exception as e:
        print(f"⚠️ 폰트 등록 중 오류: {e}")
        return 'Helvetica'  # 기본 폰트 사용

def create_company_seal():
    """회사 도장 생성 (개선된 버전)"""
    try:
        # 도장 크기 설정 (더 크게)
        seal_size = 30*mm
        
        # 도장 그리기
        drawing = Drawing(seal_size, seal_size)
        
        # 외곽 원 (빨간색, 두꺼운 테두리)
        outer_circle = Circle(seal_size/2, seal_size/2, seal_size/2 - 1*mm, 
                             strokeColor=colors.red, fillColor=None, strokeWidth=3)
        drawing.add(outer_circle)
        
        # 내부 원 (빨간색, 얇은 테두리)
        inner_circle = Circle(seal_size/2, seal_size/2, seal_size/2 - 3*mm, 
                             strokeColor=colors.red, fillColor=None, strokeWidth=1)
        drawing.add(inner_circle)
        
        # 회사명 텍스트 (중앙, 더 큰 폰트)
        company_text = String(seal_size/2, seal_size/2 + 2*mm, '온누리인쇄나라', 
                             textAnchor='middle', fontSize=10, fillColor=colors.red)
        drawing.add(company_text)
        
        # 대표자명 텍스트 (하단, 더 큰 폰트)
        ceo_text = String(seal_size/2, seal_size/2 - 2*mm, '류도현', 
                         textAnchor='middle', fontSize=8, fillColor=colors.red)
        drawing.add(ceo_text)
        
        print("✅ 도장 생성 완료")
        return drawing
        
    except Exception as e:
        print(f"⚠️ 도장 생성 중 오류: {e}")
        return None

def generate_quote_pdf(data, price_info):
    """견적서 PDF 생성 (이미지 양식과 동일하게)"""
    try:
        # PDF 버퍼 생성
        buffer = io.BytesIO()
        
        # PDF 문서 생성 (여백 최소화)
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=15*mm, leftMargin=15*mm,
                              topMargin=15*mm, bottomMargin=15*mm)
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        
        # 한글 폰트 등록
        font_name = register_korean_fonts()
        
        # 커스텀 스타일 정의
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=24,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=15,
            letterSpacing=0.2
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=4
        )
        
        # 스토리 리스트 생성
        story = []
        
        # 제목 (이미지와 동일하게)
        story.append(Paragraph("견&nbsp;&nbsp;&nbsp;적&nbsp;&nbsp;&nbsp;서", title_style))
        story.append(Spacer(1, 15))
        
        # 메인 정보 섹션 (좌우 배치) - 미리보기와 동일하게
        # 왼쪽: 수신자 정보 (일련번호, 참조, 전화번호 삭제)
        from datetime import datetime
        today = datetime.now()
        left_data = [
            ['수신', f"{data.get('customerName', '1')}"],
            ['견적일자', f"{today.year}년 {today.month}월 {today.day}일"]
        ]
        
        left_table = Table(left_data, colWidths=[25*mm, 60*mm])
        left_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f6f6f6')),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # 오른쪽: 회사 정보 (미리보기와 정확히 동일)
        right_data = [
            ['상호', '온누리인쇄나라'],
            ['사업자번호', '491-20-00640'],
            ['대표자', '류도현'],
            ['주소', '서울 금천구 가산디지털1로 142 가산더스카이밸리1차 8층 816호'],
            ['업태', '제조, 소매, 서비스업'],
            ['종목', '경인쇄, 문구, 출력, 복사, 제본'],
            ['사업자계좌번호', '신한 110-493-223413'],
            ['전화번호', '02-6338-7123']
        ]
        
        right_table = Table(right_data, colWidths=[25*mm, 60*mm])
        right_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f6f6f6')),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 주소와 종목은 왼쪽 정렬로 변경
            ('ALIGN', (1, 3), (1, 3), 'LEFT'),  # 주소
            ('ALIGN', (1, 5), (1, 5), 'LEFT'),  # 종목
        ]))
        
        # 좌우 테이블을 하나의 테이블로 결합
        combined_data = [
            [left_table, right_table]
        ]
        
        combined_table = Table(combined_data, colWidths=[85*mm, 85*mm])
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        story.append(combined_table)
        story.append(Spacer(1, 10))
        
        # 설명 문구
        story.append(Paragraph("아래와 같이 견적 합니다", normal_style))
        story.append(Spacer(1, 10))
        
        # 합계금액 섹션 (미리보기와 동일하게 설명 문구 아래에 배치)
        total_amount = price_info.get("total_price", 2220)  # 실제 계산된 금액 사용
        total_amount_korean = convert_number_to_korean(int(total_amount))
        
        total_data = [
            ['합계금액', f'₩ {total_amount:,}', '일금', f'({total_amount_korean}원)']
        ]
        
        total_table = Table(total_data, colWidths=[25*mm, 35*mm, 25*mm, 55*mm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 14),  # 폰트 크기 증가 (10 → 14)
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 10),  # 상하 패딩 증가 (8 → 10)
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 금액 부분 더 강조
            ('FONTSIZE', (1, 0), (1, 0), 16),  # 금액 폰트 더 크게
            ('FONTSIZE', (3, 0), (3, 0), 12),  # 한글 금액도 크게
        ]))
        
        story.append(total_table)
        story.append(Spacer(1, 10))
        
        # 상품 상세 테이블 (미리보기와 정확히 동일)
        item_data = [
            ['상품명', '단가적용구간', '규격', '수량', '단가', '공급가액', '세액', '비고'],
            ['흑백 단면 링제본', f"{data.get('pages', 10)}페이지", 'A4', f"{data.get('quantity', 1)}", f'₩{price_info.get("unit_price", 2220):,}', f'₩{int(price_info.get("total_price", 2220)/1.1):,}', f'₩{int(price_info.get("total_price", 2220)*0.1/1.1):,}', '']
        ]
        
        # 빈 행 3개 추가
        for _ in range(3):
            item_data.append(['', '', '', '', '', '', '', ''])
        
        item_table = Table(item_data, colWidths=[35*mm, 20*mm, 15*mm, 15*mm, 20*mm, 25*mm, 20*mm, 15*mm])
        item_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 상품명은 왼쪽 정렬
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ]))
        
        story.append(item_table)
        
        # 하단 여백
        story.append(Spacer(1, 30))
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"PDF 생성 오류: {e}")
        return None
    # 한글 폰트 등록
    font_name = register_korean_fonts()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    
    # 스타일 정의
    styles = getSampleStyleSheet()
    
    # 제목 스타일 (한글 폰트 적용)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        fontName=font_name,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # 일반 텍스트 스타일 (한글 폰트 적용)
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name,
        alignment=TA_LEFT
    )
    
    # 테이블 스타일 (한글 폰트 적용)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
    ])
    
    # 도장 먼저 생성
    company_seal = create_company_seal()
    
    # 문서 내용 구성
    story = []
    
    # 제목
    story.append(Paragraph("견적서", title_style))
    story.append(Spacer(1, 10))
    
    # 수신자 정보 테이블 (제공된 양식에 맞게 수정)
    recipient_data = [
        ['일련번호', '', '수신', data.get('customerName', '고객님') + ' 귀하'],
        ['참조', '', '전화번호', data.get('phone', '')],
        ['견적일자', '2025년 08월 11일', '', '']
    ]
    
    recipient_table = Table(recipient_data, colWidths=[30*mm, 40*mm, 20*mm, 60*mm])
    recipient_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(recipient_table)
    story.append(Spacer(1, 10))
    
    # "아래와 같이 견적합니다" 문구
    story.append(Paragraph("아래와 같이 견적합니다.", normal_style))
    story.append(Spacer(1, 10))
    
    # 공급자 정보 테이블 (제공된 양식에 맞게 수정)
    supplier_data = [
        ['공급자'],
        ['상호', '온누리인쇄나라'],
        ['사업자번호', '491-20-00640'],
        ['대표자', '류도현'],
        ['주소', '서울 금천구 가산디지털1로 142 가산더스카이밸리1차 8층 816호'],
        ['업태', '제조, 소매, 서비스업'],
        ['종목', '경인쇄, 문구, 출력, 복사, 제본'],
        ['사업자계좌번호', '신한 110-493-223413'],
        ['전화번호', '02-6338-7123']
    ]
    
    supplier_table = Table(supplier_data, colWidths=[30*mm, 120*mm])
    supplier_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
    ]))
    
    story.append(supplier_table)
    story.append(Spacer(1, 20))
    
    # 합계금액 (제공된 양식에 맞게 수정)
    total_amount = price_info['total_price']
    total_amount_korean = convert_number_to_korean(int(total_amount))
    
    total_data = [
        ['합계금액', f'일금 {total_amount_korean}원정', f'(W {total_amount:,.0f})']
    ]
    
    total_table = Table(total_data, colWidths=[30*mm, 80*mm, 40*mm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 20))
    
    # 상품명 및 상세 정보
    print_type_map = {
        'black_white': '흑백',
        'laser_color': '레이저칼라',
        'ink_color': '잉크칼라'
    }
    
    binding_type_map = {
        'ring': '링제본',
        'perfect': '무선제본',
        'saddle': '중철제본',
        'folding': '접지제본'
    }
    
    print_method_map = {
        'single': '단면',
        'double': '양면'
    }
    
    product_name = f"A4 {print_type_map.get(data.get('printType', ''), '')} {print_method_map.get(data.get('printMethod', ''), '')} {binding_type_map.get(data.get('bindingType', ''), '')}"
    
    # 상품 상세 테이블 (제공된 양식에 맞게 수정)
    item_data = [
        ['상품명', '단가적용구간', '규격', '수량', '단가', '공급가액', '세액', '비고'],
        [product_name, '', '', str(data.get('quantity', '')), 
         f"{price_info['unit_price']:,.0f}", 
         f"{price_info['total_price']:,.0f}", 
         f"{price_info['total_price'] * 0.1:,.0f}", '']
    ]
    
    item_table = Table(item_data, colWidths=[40*mm, 25*mm, 20*mm, 15*mm, 20*mm, 25*mm, 20*mm, 25*mm])
    item_table.setStyle(table_style)
    
    story.append(item_table)
    
    # 서명 및 도장 영역 추가 (도장을 먼저 그리고 그 위에 서명 정보 올리기)
    story.append(Spacer(1, 30))
    
    # 도장과 서명을 함께 배치하는 테이블 생성
    if company_seal:
        # 도장과 서명 정보를 한 테이블에 배치
        signature_seal_data = [
            ['', '', '', company_seal],
            ['', '', '', ''],
            ['', '온누리인쇄나라', '', ''],
            ['', '대표: 류도현', '', ''],
            ['', '2025년 08월 11일', '', '']
        ]
        
        signature_seal_table = Table(signature_seal_data, colWidths=[40*mm, 50*mm, 20*mm, 40*mm])
        signature_seal_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),  # 도장 오른쪽 정렬
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (1, 2), (1, 2), 1, colors.black),  # 회사명 아래 선
            ('LINEBELOW', (1, 3), (1, 3), 1, colors.black),  # 대표명 아래 선
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        story.append(signature_seal_table)
    else:
        # 도장이 없는 경우 기본 서명 테이블
        signature_data = [
            ['', '', ''],
            ['', '', ''],
            ['', '온누리인쇄나라', ''],
            ['', '대표: 류도현', ''],
            ['', datetime.now().strftime('%Y년 %m월 %d일'), '']
        ]
        
        signature_table = Table(signature_data, colWidths=[60*mm, 60*mm, 30*mm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (1, 2), (1, 2), 1, colors.black),  # 회사명 아래 선
            ('LINEBELOW', (1, 3), (1, 3), 1, colors.black),  # 대표명 아래 선
        ]))
        
        story.append(signature_table)
    
    # PDF 생성
    doc.build(story)
    buffer.seek(0)
    return buffer

def ensure_db():
    """gunicorn 환경에서도 최초 로드시 DB 테이블을 보장 생성"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ DB 초기화 완료")
    except Exception as e:
        print(f"DB 초기화 오류: {e}")

def safe_int_conversion(value):
    """안전한 정수 변환 함수"""
    try:
        if value is None or value == '':
            return 0
        
        if isinstance(value, str):
            # 빈 문자열이나 공백 처리
            value = value.strip()
            if not value:
                return 0
            
            # 소수점이 있는 경우 처리
            if '.' in value:
                return int(float(value))
            else:
                return int(value)
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return int(str(value))
    except (ValueError, TypeError):
        print(f"정수 변환 오류: {value}")
        return 0

def convert_number_to_korean(number):
    """숫자를 한글로 변환 (개선된 버전)"""
    if number == 0:
        return '영'
    
    # 한글 숫자 매핑
    units = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    tens = ['', '십', '백', '천']
    big_units = ['', '만', '억', '조']
    
    # 숫자를 문자열로 변환하고 뒤집기
    num_str = str(number)[::-1]
    result = []
    
    for i, digit in enumerate(num_str):
        if digit == '0':
            continue
            
        # 큰 단위 (만, 억, 조)
        if i % 4 == 0 and i > 0:
            big_unit_idx = i // 4
            if big_unit_idx < len(big_units):
                result.append(big_units[big_unit_idx])
        
        # 작은 단위 (십, 백, 천)
        small_unit_idx = i % 4
        if small_unit_idx > 0 and digit != '1':
            result.append(tens[small_unit_idx])
        elif small_unit_idx > 0 and digit == '1':
            result.append(tens[small_unit_idx])
        
        # 숫자
        if digit != '1' or small_unit_idx == 0:
            result.append(units[int(digit)])
    
    # 결과 뒤집기
    result.reverse()
    return ''.join(result)

# 폴더 관리 관련 라우트들
@app.route('/api/folders', methods=['GET'])
def get_folders():
    """폴더 목록 조회"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        folders_file = os.path.join(upload_folder, 'folders.json')
        
        if os.path.exists(folders_file):
            with open(folders_file, 'r', encoding='utf-8') as f:
                folders = json.load(f)
        else:
            # 기본 폴더들 생성
            folders = [
                {'id': 'ring', 'name': '링제본', 'description': '링제본 작업 사진'},
                {'id': 'perfect', 'name': '무선제본', 'description': '무선제본 작업 사진'},
                {'id': 'saddle', 'name': '중철제본', 'description': '중철제본 작업 사진'},
                {'id': 'folding', 'name': '접지제본', 'description': '접지제본 작업 사진'},
                {'id': 'academy', 'name': '학원교재', 'description': '학원교재 관련 작업 사진'},
                {'id': 'company', 'name': '회사소개서', 'description': '회사소개서 관련 작업 사진'}
            ]
            # 기본 폴더들 저장
            with open(folders_file, 'w', encoding='utf-8') as f:
                json.dump(folders, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'folders': folders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/folders', methods=['POST'])
@login_required
def create_folder():
    """새 폴더 생성 (관리자 전용)"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': '관리자 권한이 필요합니다.'})
        
        data = request.get_json()
        folder_name = data.get('name', '').strip()
        folder_description = data.get('description', '').strip()
        
        if not folder_name:
            return jsonify({'success': False, 'error': '폴더명을 입력해주세요.'})
        
        upload_folder = app.config['UPLOAD_FOLDER']
        folders_file = os.path.join(upload_folder, 'folders.json')
        
        # 기존 폴더 목록 읽기
        folders = []
        if os.path.exists(folders_file):
            with open(folders_file, 'r', encoding='utf-8') as f:
                folders = json.load(f)
        
        # 폴더명 중복 확인
        if any(folder['name'] == folder_name for folder in folders):
            return jsonify({'success': False, 'error': '이미 존재하는 폴더명입니다.'})
        
        # 새 폴더 추가
        new_folder = {
            'id': str(uuid.uuid4()),
            'name': folder_name,
            'description': folder_description,
            'created_date': datetime.now().isoformat(),
            'created_by': 'admin'  # 실제로는 현재 사용자 ID
        }
        
        folders.append(new_folder)
        
        # 폴더 목록 저장
        with open(folders_file, 'w', encoding='utf-8') as f:
            json.dump(folders, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': '폴더가 생성되었습니다.', 'folder': new_folder})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/folders/<folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    """폴더 삭제 (관리자 전용)"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': '관리자 권한이 필요합니다.'})
        
        upload_folder = app.config['UPLOAD_FOLDER']
        folders_file = os.path.join(upload_folder, 'folders.json')
        
        if not os.path.exists(folders_file):
            return jsonify({'success': False, 'error': '폴더를 찾을 수 없습니다.'})
        
        # 폴더 목록 읽기
        with open(folders_file, 'r', encoding='utf-8') as f:
            folders = json.load(f)
        
        # 삭제할 폴더 찾기
        folder_to_delete = None
        for folder in folders:
            if folder['id'] == folder_id:
                folder_to_delete = folder
                break
        
        if not folder_to_delete:
            return jsonify({'success': False, 'error': '폴더를 찾을 수 없습니다.'})
        
        # 기본 폴더는 삭제 불가
        default_folders = ['ring', 'perfect', 'saddle', 'folding', 'academy', 'company']
        if folder_to_delete['id'] in default_folders:
            return jsonify({'success': False, 'error': '기본 폴더는 삭제할 수 없습니다.'})
        
        # 해당 폴더의 사진들 확인
        metadata_file = os.path.join(upload_folder, 'photos_metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                photos = json.load(f)
            
            folder_photos = [p for p in photos if p.get('folder_id') == folder_id]
            if folder_photos:
                return jsonify({'success': False, 'error': f'폴더에 {len(folder_photos)}개의 사진이 있습니다. 먼저 사진을 삭제해주세요.'})
        
        # 폴더 삭제
        folders = [f for f in folders if f['id'] != folder_id]
        
        # 폴더 목록 저장
        with open(folders_file, 'w', encoding='utf-8') as f:
            json.dump(folders, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': '폴더가 삭제되었습니다.'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 작업 사진 갤러리 관련 라우트들
@app.route('/api/photos', methods=['GET'])
def get_photos():
    """업로드된 작업 사진 목록 조회"""
    try:
        photos = []
        upload_folder = app.config['UPLOAD_FOLDER']
        
        # 업로드 폴더가 없으면 생성
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # 메타데이터 파일에서 사진 정보 읽기
        metadata_file = os.path.join(upload_folder, 'photos_metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                photos = json.load(f)
        
        return jsonify({'success': True, 'photos': photos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/photos', methods=['POST'])
@login_required
def upload_photo():
    """작업 사진 업로드 (관리자 전용)"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': '관리자 권한이 필요합니다.'})
        
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'})
        
        file = request.files['photo']
        folder_id = request.form.get('folder_id')
        description = request.form.get('description', '')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'})
        
        if not folder_id:
            return jsonify({'success': False, 'error': '폴더를 선택해주세요.'})
        
        if file and allowed_file(file.filename):
            # 파일명 보안 처리
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # 업로드 폴더 생성
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # 파일 저장
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # 메타데이터 저장
            photo_data = {
                'id': str(uuid.uuid4()),
                'filename': unique_filename,
                'original_name': filename,
                'folder_id': folder_id,
                'description': description,
                'upload_date': datetime.now().isoformat(),
                'file_size': os.path.getsize(file_path)
            }
            
            # 기존 메타데이터 읽기
            metadata_file = os.path.join(upload_folder, 'photos_metadata.json')
            photos = []
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    photos = json.load(f)
            
            # 새 사진 추가
            photos.append(photo_data)
            
            # 메타데이터 저장
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(photos, f, ensure_ascii=False, indent=2)
            
            return jsonify({'success': True, 'message': '사진이 성공적으로 업로드되었습니다.'})
        else:
            return jsonify({'success': False, 'error': '지원하지 않는 파일 형식입니다.'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/photos/<photo_id>', methods=['DELETE'])
@login_required
def delete_photo(photo_id):
    """작업 사진 삭제 (관리자 전용)"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': '관리자 권한이 필요합니다.'})
        
        upload_folder = app.config['UPLOAD_FOLDER']
        metadata_file = os.path.join(upload_folder, 'photos_metadata.json')
        
        if not os.path.exists(metadata_file):
            return jsonify({'success': False, 'error': '사진을 찾을 수 없습니다.'})
        
        # 메타데이터 읽기
        with open(metadata_file, 'r', encoding='utf-8') as f:
            photos = json.load(f)
        
        # 삭제할 사진 찾기
        photo_to_delete = None
        for photo in photos:
            if photo['id'] == photo_id:
                photo_to_delete = photo
                break
        
        if not photo_to_delete:
            return jsonify({'success': False, 'error': '사진을 찾을 수 없습니다.'})
        
        # 파일 삭제
        file_path = os.path.join(upload_folder, photo_to_delete['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 메타데이터에서 제거
        photos = [p for p in photos if p['id'] != photo_id]
        
        # 메타데이터 저장
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(photos, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': '사진이 삭제되었습니다.'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """업로드된 파일 서빙"""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("🚀 온누리인쇄나라 강화된 웹사이트를 시작합니다...")
    print("📱 브라우저에서 http://localhost:5000 으로 접속하세요.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
