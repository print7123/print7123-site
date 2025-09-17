// 온누리인쇄나라 전용 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 견적 계산 폼 처리
    const quoteForm = document.getElementById('quoteForm');
    if (quoteForm) {
        quoteForm.addEventListener('submit', handleQuoteCalculation);
    }
    
    // 스크롤 애니메이션
    initScrollAnimations();
    
    // 부드러운 스크롤
    initSmoothScroll();
});

// 견적 계산 처리 (버튼 클릭 이벤트용)
function handleQuoteCalculation(e) {
    if (e) {
        e.preventDefault();
    }
    
    console.log('견적 계산 함수 시작');
    
    // 폼 데이터 수집
    const formData = {
        customerName: document.getElementById('customerName').value,
        email: document.getElementById('email') ? document.getElementById('email').value : '',
        pages: parseInt(document.getElementById('pages').value),
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: parseInt(document.getElementById('quantity').value)
    };
    
    console.log('폼 데이터:', formData);
    
    // 필수 필드 검증
    if (!formData.customerName || !formData.pages || !formData.printType || !formData.bindingType || !formData.quantity) {
        showAlert('모든 필수 항목을 입력해주세요.', 'warning');
        return;
    }
    
    // 로딩 표시
    const calculateBtn = document.getElementById('calculateBtn');
    if (!calculateBtn) {
        console.error('calculateBtn 요소를 찾을 수 없습니다');
        showAlert('견적 계산 버튼을 찾을 수 없습니다.', 'danger');
        return;
    }
    
    const originalText = calculateBtn.innerHTML;
    calculateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>견적 계산 중...';
    calculateBtn.disabled = true;
    
    console.log('견적 계산 요청 시작');
    
    // 견적 계산 API 호출
    fetch('/quote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('견적 계산 응답 상태:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('견적 계산 응답 데이터:', data);
        displayQuoteResult(data, formData);
    })
    .catch(error => {
        console.error('견적 계산 오류:', error);
        showAlert('견적 계산 중 오류가 발생했습니다: ' + error.message, 'danger');
    })
    .finally(() => {
        // 버튼 상태 복원
        calculateBtn.innerHTML = originalText;
        calculateBtn.disabled = false;
        console.log('견적 계산 함수 완료');
    });
}

// 견적 결과 표시
function displayQuoteResult(data, formData) {
    const resultDiv = document.getElementById('quoteResult');
    
    if (!resultDiv) {
        console.error('quoteResult 요소를 찾을 수 없습니다');
        showAlert('견적 결과를 표시할 영역을 찾을 수 없습니다.', 'danger');
        return;
    }
    
    console.log('견적 결과 표시 시작:', data);
    
    // 결과 데이터 설정
    const unitPrintPriceEl = document.getElementById('unitPrintPrice');
    const printPriceEl = document.getElementById('printPrice');
    const bindingPriceEl = document.getElementById('bindingPrice');
    const totalBindingPriceEl = document.getElementById('totalBindingPrice');
    const unitPriceEl = document.getElementById('unitPrice');
    const quantityResultEl = document.getElementById('quantityResult');
    const totalPriceEl = document.getElementById('totalPrice');
    
    if (unitPrintPriceEl) unitPrintPriceEl.textContent = data.unit_print_price.toLocaleString();
    if (printPriceEl) printPriceEl.textContent = data.print_price.toLocaleString();
    if (bindingPriceEl) bindingPriceEl.textContent = data.unit_binding_price.toLocaleString();
    
    // 총 제본 비용 표시 (서버에서 이미 총 비용으로 계산됨)
    if (totalBindingPriceEl) totalBindingPriceEl.textContent = data.binding_price.toLocaleString();
    
    if (unitPriceEl) unitPriceEl.textContent = data.unit_price.toLocaleString();
    if (quantityResultEl) quantityResultEl.textContent = formData.quantity;
    // 총 가격 표시 (부가세 포함된 금액)
    if (totalPriceEl) totalPriceEl.textContent = data.total_price_with_tax.toLocaleString();
    
    // 총 페이지 수 표시
    if (data.total_pages) {
        const totalPagesElement = document.getElementById('totalPages');
        if (totalPagesElement) {
            totalPagesElement.textContent = data.total_pages.toLocaleString();
        }
    }
    
    // 잉크칼라 선택 시 특별 안내 메시지
    if (formData.printType === 'ink_color') {
        const inkColorInfo = document.getElementById('inkColorInfo');
        if (inkColorInfo) {
            inkColorInfo.style.display = 'block';
        }
    } else {
        const inkColorInfo = document.getElementById('inkColorInfo');
        if (inkColorInfo) {
            inkColorInfo.style.display = 'none';
        }
    }
    
    // 결과 표시
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth' });
    
    // PDF 버튼 표시
    
    // 결제 버튼 표시
    const paymentBtn = document.getElementById('paymentBtn');
    if (paymentBtn) {
        paymentBtn.style.display = 'inline-block';
    }
    
    // 성공 알림
    showAlert('견적이 계산되었습니다!', 'success');
}

// 메일로 파일 첨부 주문
function emailOrder() {
    // 견적 정보 수집
    const formData = {
        customerName: document.getElementById('customerName').value,
        pages: document.getElementById('pages').value,
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: document.getElementById('quantity').value,
        size: document.getElementById('size').value
    };
    
    // 필수 정보 확인
    if (!formData.customerName || !formData.pages || !formData.quantity) {
        showAlert('견적 정보를 모두 입력해주세요.', 'warning');
        return;
    }
    
    // 메일 주문 모달 표시
    showEmailOrderModal(formData);
}


// 카톡 주문 진행
function kakaoOrder() {
    // 견적 정보 수집
    const formData = {
        customerName: document.getElementById('customerName').value,
        pages: document.getElementById('pages').value,
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: document.getElementById('quantity').value,
        size: document.getElementById('size').value
    };
    
    // 필수 정보 확인
    if (!formData.customerName || !formData.pages || !formData.quantity) {
        showAlert('견적 정보를 모두 입력해주세요.', 'warning');
            return;
        }
        
    // 카톡 주문 모달 표시
    showKakaoOrderModal(formData);
}

// 카톡 주문 모달 표시
function showKakaoOrderModal(formData) {
    const totalPrice = document.getElementById('totalPrice').textContent;
    
    const modalHtml = `
        <div class="modal fade" id="kakaoOrderModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fab fa-telegram-plane me-2"></i>카톡으로 파일 전송
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-4">
                            <h4 class="text-warning">💬 카카오톡 주문 안내</h4>
                            <p class="lead">카톡으로 파일을 전송하고 주문하세요!</p>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card border-warning">
                                    <div class="card-body text-center">
                                        <h5 class="card-title text-warning">
                                            <i class="fab fa-telegram-plane me-2"></i>카톡 연락처
                                        </h5>
                                        <h3 class="text-primary fw-bold">010-2624-7123</h3>
                                        <p class="text-muted">24시간 접수 가능</p>
                                        <a href="http://pf.kakao.com/_kjRIj" target="_blank" class="btn btn-warning btn-lg">
                                            <i class="fab fa-telegram-plane me-2"></i>카톡 플러스 친구 추가
                                        </a>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-info">
                                    <div class="card-body">
                                        <h5 class="card-title text-info">
                                            <i class="fas fa-clipboard-list me-2"></i>견적 정보
                                        </h5>
                                        <ul class="list-unstyled">
                                            <li><strong>고객명:</strong> ${formData.customerName}</li>
                                            <li><strong>페이지:</strong> ${formData.pages}페이지</li>
                                            <li><strong>인쇄방식:</strong> ${formData.printType}</li>
                                            <li><strong>제본방식:</strong> ${formData.bindingType}</li>
                                            <li><strong>수량:</strong> ${formData.quantity}권</li>
                                            <li><strong>총 가격:</strong> <span class="text-primary fw-bold">${totalPrice}</span></li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="alert alert-warning mt-3">
                            <h6><i class="fas fa-info-circle me-2"></i>카톡 주문 시 안내사항</h6>
                            <ul class="mb-0">
                                <li>위 견적 정보를 카톡 메시지에 포함해주세요</li>
                                <li>인쇄할 파일을 카톡으로 전송해주세요</li>
                                <li>파일 형식: PDF, AI, PSD, JPG, PNG 등</li>
                                <li>연락처와 배송 주소를 함께 전송해주세요</li>
                                <li>카톡 접수 후 빠른 시간 내에 확인 연락드립니다</li>
                                <li>대용량 파일도 카톡으로 전송 가능합니다</li>
                            </ul>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-body text-center">
                                <h6 class="card-title text-primary">
                                    <i class="fas fa-mobile-alt me-2"></i>간편 주문 방법
                                </h6>
                                <p class="mb-0">위 버튼을 클릭하면 카톡 플러스 친구로 바로 이동하여<br>견적 정보와 파일을 전송할 수 있습니다!</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('kakaoOrderModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('kakaoOrderModal'));
    modal.show();
}

// 웹메일 클라이언트 열기
function openEmailClient(customerName, pages, printType, bindingType, quantity, totalPrice) {
    // 견적 정보 텍스트 생성
    const quoteInfo = `견적 정보:
- 고객명: ${customerName}
- 페이지: ${pages}페이지
- 인쇄방식: ${printType}
- 제본방식: ${bindingType}
- 수량: ${quantity}권
- 총 가격: ${totalPrice}

파일을 첨부하여 주문해주세요!`;
    
    // 웹메일 선택 모달 표시
    const modalHtml = `
        <div class="modal fade" id="emailClientModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-envelope me-2"></i>메일 서비스 선택
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <p class="mb-4">어떤 메일 서비스를 사용하시나요?</p>
                        <div class="row g-3">
                            <div class="col-md-6">
                                <button class="btn btn-outline-primary btn-lg w-100" onclick="openGmail('${customerName}', '${pages}', '${printType}', '${bindingType}', '${quantity}', '${totalPrice}')">
                                    <i class="fab fa-google me-2"></i>Gmail
                                </button>
                            </div>
                            <div class="col-md-6">
                                <button class="btn btn-outline-success btn-lg w-100" onclick="openNaverMail('${customerName}', '${pages}', '${printType}', '${bindingType}', '${quantity}', '${totalPrice}')">
                                    <i class="fas fa-envelope me-2"></i>네이버 메일
                                </button>
                            </div>
                            <div class="col-md-6">
                                <button class="btn btn-outline-info btn-lg w-100" onclick="openDaumMail('${customerName}', '${pages}', '${printType}', '${bindingType}', '${quantity}', '${totalPrice}')">
                                    <i class="fas fa-envelope me-2"></i>다음 메일
                                </button>
                            </div>
                            <div class="col-md-6">
                                <button class="btn btn-outline-secondary btn-lg w-100" onclick="copyEmailInfo('${customerName}', '${pages}', '${printType}', '${bindingType}', '${quantity}', '${totalPrice}')">
                                    <i class="fas fa-copy me-2"></i>이메일 정보 복사
                                </button>
                            </div>
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">선택한 메일 서비스로 이동하여 견적 정보가 자동으로 입력됩니다</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('emailClientModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('emailClientModal'));
    modal.show();
}

// Gmail 열기
function openGmail(customerName, pages, printType, bindingType, quantity, totalPrice) {
    // Gmail 페이지로 이동
    const gmailUrl = `https://mail.google.com/mail/u/0/#inbox`;
    window.open(gmailUrl, '_blank');
    
    // 견적 정보를 클립보드에 복사하여 사용자가 붙여넣기 할 수 있도록 함
    const emailInfo = `받는 사람: print7123@naver.com
제목: 인쇄주문-${customerName}

견적 정보:
- 고객명: ${customerName}
- 페이지: ${pages}페이지
- 인쇄방식: ${printType}
- 제본방식: ${bindingType}
- 수량: ${quantity}권
- 총 가격: ${totalPrice}

파일을 첨부하여 주문해주세요!`;
    
    navigator.clipboard.writeText(emailInfo).then(() => {
        showAlert('Gmail로 이동했습니다. 견적 정보가 클립보드에 복사되었으니 붙여넣기 하세요!', 'info');
    }).catch(() => {
        showAlert('Gmail로 이동했습니다. 견적 정보를 수동으로 입력해주세요.', 'info');
    });
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('emailClientModal'));
    modal.hide();
}

// 네이버 메일 열기
function openNaverMail(customerName, pages, printType, bindingType, quantity, totalPrice) {
    // 네이버 메일 작성 페이지로 이동
    const naverUrl = `https://mail.naver.com/v2/folders/0/all`;
    window.open(naverUrl, '_blank');
    
    // 견적 정보를 클립보드에 복사하여 사용자가 붙여넣기 할 수 있도록 함
    const emailInfo = `받는 사람: print7123@naver.com
제목: 인쇄주문-${customerName}

견적 정보:
- 고객명: ${customerName}
- 페이지: ${pages}페이지
- 인쇄방식: ${printType}
- 제본방식: ${bindingType}
- 수량: ${quantity}권
- 총 가격: ${totalPrice}

파일을 첨부하여 주문해주세요!`;
    
    navigator.clipboard.writeText(emailInfo).then(() => {
        showAlert('네이버 메일로 이동했습니다. 견적 정보가 클립보드에 복사되었으니 붙여넣기 하세요!', 'info');
    }).catch(() => {
        showAlert('네이버 메일로 이동했습니다. 견적 정보를 수동으로 입력해주세요.', 'info');
    });
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('emailClientModal'));
    modal.hide();
}

// 다음 메일 열기
function openDaumMail(customerName, pages, printType, bindingType, quantity, totalPrice) {
    // 다음 메일 페이지로 이동
    const daumUrl = `https://mail.daum.net/top/INBOX`;
    window.open(daumUrl, '_blank');
    
    // 견적 정보를 클립보드에 복사하여 사용자가 붙여넣기 할 수 있도록 함
    const emailInfo = `받는 사람: print7123@naver.com
제목: 인쇄주문-${customerName}

견적 정보:
- 고객명: ${customerName}
- 페이지: ${pages}페이지
- 인쇄방식: ${printType}
- 제본방식: ${bindingType}
- 수량: ${quantity}권
- 총 가격: ${totalPrice}

파일을 첨부하여 주문해주세요!`;
    
    navigator.clipboard.writeText(emailInfo).then(() => {
        showAlert('다음 메일로 이동했습니다. 견적 정보가 클립보드에 복사되었으니 붙여넣기 하세요!', 'info');
    }).catch(() => {
        showAlert('다음 메일로 이동했습니다. 견적 정보를 수동으로 입력해주세요.', 'info');
    });
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('emailClientModal'));
    modal.hide();
}

// 이메일 정보 복사
function copyEmailInfo(customerName, pages, printType, bindingType, quantity, totalPrice) {
    const emailInfo = `받는 사람: print7123@naver.com
제목: 인쇄주문-${customerName}

견적 정보:
- 고객명: ${customerName}
- 페이지: ${pages}페이지
- 인쇄방식: ${printType}
- 제본방식: ${bindingType}
- 수량: ${quantity}권
- 총 가격: ${totalPrice}

파일을 첨부하여 주문해주세요!`;
    
    navigator.clipboard.writeText(emailInfo).then(() => {
        showAlert('이메일 정보가 클립보드에 복사되었습니다!', 'success');
    }).catch(() => {
        // 클립보드 복사 실패 시 대체 방법
        const textArea = document.createElement('textarea');
        textArea.value = emailInfo;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('이메일 정보가 복사되었습니다!', 'success');
    });
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('emailClientModal'));
    modal.hide();
}

// 카톡 연락처 복사 기능
function copyKakaoInfo() {
    const kakaoInfo = `온누리인쇄나라 카톡 주문
연락처: 010-2624-7123
전화: 02-6338-7123
이메일: print7123@naver.com

견적 정보:
- 고객명: ${document.getElementById('customerName').value}
- 페이지: ${document.getElementById('pages').value}페이지
- 인쇄방식: ${document.getElementById('printType').value}
- 제본방식: ${document.getElementById('bindingType').value}
- 수량: ${document.getElementById('quantity').value}권
- 총 가격: ${document.getElementById('totalPrice').textContent}

파일을 첨부하여 주문해주세요!`;
    
    navigator.clipboard.writeText(kakaoInfo).then(() => {
        showAlert('카톡 주문 정보가 클립보드에 복사되었습니다!', 'success');
    }).catch(() => {
        // 클립보드 복사 실패 시 대체 방법
        const textArea = document.createElement('textarea');
        textArea.value = kakaoInfo;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('카톡 주문 정보가 복사되었습니다!', 'success');
    });
}

// 메일 주문 모달 표시
function showEmailOrderModal(formData) {
    const totalPrice = document.getElementById('totalPrice').textContent;
    
    const modalHtml = `
        <div class="modal fade" id="emailOrderModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-envelope me-2"></i>메일로 파일 첨부 주문
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-4">
                            <h4 class="text-success">📧 이메일 주문 안내</h4>
                            <p class="lead">파일을 첨부하여 이메일로 주문하세요!</p>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card border-success">
                                    <div class="card-body text-center">
                                        <h5 class="card-title text-success">
                                            <i class="fas fa-envelope me-2"></i>이메일 주소
                                        </h5>
                                        <h3 class="text-primary fw-bold">print7123@naver.com</h3>
                                        <p class="text-muted">24시간 접수 가능</p>
                                        <div class="d-grid gap-2">
                                            <button class="btn btn-success btn-lg" onclick="openEmailClient('${formData.customerName}', '${formData.pages}', '${formData.printType}', '${formData.bindingType}', '${formData.quantity}', '${totalPrice}')">
                                                <i class="fas fa-envelope me-2"></i>메일 주문하기
                                            </button>
                                            <div class="text-center">
                                                <small class="text-muted">웹메일로 바로 이동합니다</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-info">
                                    <div class="card-body">
                                        <h5 class="card-title text-info">
                                            <i class="fas fa-clipboard-list me-2"></i>견적 정보
                                        </h5>
                                        <ul class="list-unstyled">
                                            <li><strong>고객명:</strong> ${formData.customerName}</li>
                                            <li><strong>페이지:</strong> ${formData.pages}페이지</li>
                                            <li><strong>인쇄방식:</strong> ${formData.printType}</li>
                                            <li><strong>제본방식:</strong> ${formData.bindingType}</li>
                                            <li><strong>수량:</strong> ${formData.quantity}권</li>
                                            <li><strong>총 가격:</strong> <span class="text-primary fw-bold">${totalPrice}</span></li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="alert alert-success mt-3">
                            <h6><i class="fas fa-info-circle me-2"></i>이메일 주문 시 안내사항</h6>
                            <ul class="mb-0">
                                <li>위 견적 정보를 메일 제목에 포함해주세요</li>
                                <li>인쇄할 파일을 첨부하여 보내주세요</li>
                                <li>연락처와 배송 주소를 메일 내용에 포함해주세요</li>
                                <li>이메일 접수 후 24시간 내에 확인 연락드립니다</li>
                            </ul>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('emailOrderModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('emailOrderModal'));
    modal.show();
}


// 전화 주문 모달 표시
function showPhoneOrderModal(formData) {
    const totalPrice = document.getElementById('totalPrice').textContent;
    
    const modalHtml = `
        <div class="modal fade" id="phoneOrderModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fas fa-phone me-2"></i>전화 주문 안내
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-4">
                            <h4 class="text-warning">📞 전화 주문 상담</h4>
                            <p class="lead">전문 상담원이 친절하게 도와드립니다!</p>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card border-warning">
                                    <div class="card-body text-center">
                                        <h5 class="card-title text-warning">
                                            <i class="fas fa-phone-alt me-2"></i>전화번호
                                        </h5>
                                        <h3 class="text-primary fw-bold">02-6338-7123</h3>
                                        <p class="text-muted">평일 09:00-16:00</p>
                                        <a href="tel:02-6338-7123" class="btn btn-warning btn-lg">
                                            <i class="fas fa-phone me-2"></i>지금 전화하기
                                        </a>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-info">
                                    <div class="card-body">
                                        <h5 class="card-title text-info">
                                            <i class="fas fa-clipboard-list me-2"></i>견적 정보
                                        </h5>
                                        <ul class="list-unstyled">
                                            <li><strong>고객명:</strong> ${formData.customerName}</li>
                                            <li><strong>페이지:</strong> ${formData.pages}페이지</li>
                                            <li><strong>인쇄방식:</strong> ${formData.printType}</li>
                                            <li><strong>제본방식:</strong> ${formData.bindingType}</li>
                                            <li><strong>수량:</strong> ${formData.quantity}권</li>
                                            <li><strong>총 가격:</strong> <span class="text-primary fw-bold">${totalPrice}</span></li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="alert alert-info mt-3">
                            <h6><i class="fas fa-info-circle me-2"></i>전화 주문 시 안내사항</h6>
                            <ul class="mb-0">
                                <li>위 견적 정보를 바탕으로 상담원이 정확한 견적을 제공합니다</li>
                                <li>추가 요구사항이나 수정사항이 있으시면 전화에서 말씀해 주세요</li>
                                <li>전화 주문 시 추가 할인 혜택이 있을 수 있습니다</li>
                                <li>배송 및 납기일 문의도 함께 가능합니다</li>
                            </ul>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                        <a href="tel:02-6338-7123" class="btn btn-warning btn-lg">
                            <i class="fas fa-phone me-2"></i>전화 주문하기
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('phoneOrderModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('phoneOrderModal'));
    modal.show();
}

// 기존 함수들 (호환성을 위해 유지)
function proceedToOrder() {
    emailOrder();
}

function onlineOrder() {
    emailOrder();
}

function phoneOrder() {
    kakaoOrder();
}

// 네이버플레이스 연동 옵션 표시
function showNaverPlaceOption(priceInfo) {
    const modalHtml = `
        <div class="modal fade" id="naverPlaceModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">주문 및 방문 안내</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-4">
                            <h4>총 금액: ₩${priceInfo.total_price.toLocaleString()}</h4>
                            <p class="text-muted">견적서가 생성되었습니다. 주문 방법을 선택해주세요.</p>
                        </div>
                        
                        <!-- 가게 위치 정보 -->
                        <div class="card mb-4">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0"><i class="fas fa-map-marker-alt me-2"></i>온누리인쇄나라 위치</h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p class="mb-2"><strong>주소:</strong> 서울 금천구 가산디지털1로 142 가산더스카이밸리1차 8층 816호</p>
                                        <p class="mb-2"><strong>전화:</strong> 02-6338-7123</p>
                                        <p class="mb-2"><strong>운영시간:</strong> 평일 09:00-18:00</p>
                                    </div>
                                    <div class="col-md-6">
                                        <div id="mapContainer" style="height: 200px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                                            <div class="text-center">
                                                <i class="fas fa-map fa-3x text-muted mb-2"></i>
                                                <p class="text-muted">지도 로딩 중...</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="d-grid gap-2">
                            <button class="btn btn-success btn-lg" onclick="openNaverPlace()">
                                <i class="fas fa-store me-2"></i>네이버플레이스에서 주문
                            </button>
                            <button class="btn btn-primary btn-lg" onclick="openNaverShopping()">
                                <i class="fas fa-shopping-cart me-2"></i>네이버쇼핑에서 주문
                            </button>
                            <button class="btn btn-info btn-lg" onclick="openKakaoTalk()">
                                <i class="fas fa-comments me-2"></i>카카오톡으로 문의
                            </button>
                            <button class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                나중에 주문하기
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('naverPlaceModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('naverPlaceModal'));
    modal.show();
    
    // 지도 로드
    loadMap();
}

// 네이버플레이스 열기
function openNaverPlace() {
    // 네이버플레이스 URL (온누리인쇄나라)
    const naverPlaceUrl = 'https://map.naver.com/v5/search/온누리인쇄나라/place/1234567890';
    window.open(naverPlaceUrl, '_blank');
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('naverPlaceModal'));
    modal.hide();
}

// 카카오톡 문의 열기
function openKakaoTalk() {
    const kakaoTalkUrl = 'https://pf.kakao.com/_print7123';
    window.open(kakaoTalkUrl, '_blank');
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('naverPlaceModal'));
    modal.hide();
}

// 지도 로드 함수
function loadMap() {
    // 간단한 지도 표시 (실제 구현 시 네이버 지도 API 사용)
    setTimeout(() => {
        const mapContainer = document.getElementById('mapContainer');
        if (mapContainer) {
            mapContainer.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-map-marker-alt fa-3x text-danger mb-2"></i>
                    <p class="mb-1"><strong>온누리인쇄나라</strong></p>
                    <p class="text-muted small">서울 금천구 가산디지털1로 142</p>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="openNaverMap()">
                        <i class="fas fa-external-link-alt me-1"></i>네이버 지도에서 보기
                    </button>
                </div>
            `;
        }
    }, 1000);
}

// 네이버 지도 열기
function openNaverMap() {
    const naverMapUrl = 'https://map.naver.com/v5/search/온누리인쇄나라';
    window.open(naverMapUrl, '_blank');
}

// 네이버쇼핑 열기
function openNaverShopping() {
    const formData = {
        customerName: document.getElementById('customerName').value,
        pages: document.getElementById('pages').value,
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: document.getElementById('quantity').value,
        size: document.getElementById('size').value
    };
    
    const naverShoppingUrl = `https://smartstore.naver.com/print7123/products/자동견적-${formData.customerName}-${formData.pages}페이지-${formData.quantity}부`;
    window.open(naverShoppingUrl, '_blank');
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('naverPlaceModal'));
    modal.hide();
}

// 견적서 미리보기 함수
function previewQuote() {
    console.log('견적서 미리보기 시작');
    
    const formData = {
        customerName: document.getElementById('customerName').value,
        email: document.getElementById('email') ? document.getElementById('email').value : '',
        pages: parseInt(document.getElementById('pages').value),
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: parseInt(document.getElementById('quantity').value)
    };
    
    // 필수 필드 확인
    if (!formData.customerName || !formData.pages || !formData.printType || !formData.bindingType || !formData.quantity) {
        showAlert('모든 필드를 입력해주세요.', 'warning');
        return;
    }
    
    // 로딩 표시
    const previewBtn = document.getElementById('previewBtn');
    if (!previewBtn) {
        console.error('previewBtn 요소를 찾을 수 없습니다');
        showAlert('미리보기 버튼을 찾을 수 없습니다.', 'danger');
        return;
    }
    
    const originalText = previewBtn.innerHTML;
    previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>미리보기 생성 중...';
    previewBtn.disabled = true;
    
    console.log('미리보기 요청 시작');
    
    // 미리보기 요청
    fetch('/preview_quote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('미리보기 응답 상태:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('미리보기 응답 데이터:', data);
        if (data.success) {
            showTextPreview(data.price_info);
        } else {
            throw new Error(data.error || '미리보기 생성 실패');
        }
    })
    .catch(error => {
        console.error('미리보기 오류:', error);
        showAlert('미리보기 생성 중 오류가 발생했습니다: ' + error.message, 'danger');
    })
    .finally(() => {
        // 버튼 상태 복원
        previewBtn.innerHTML = originalText;
        previewBtn.disabled = false;
        console.log('미리보기 함수 완료');
    });
}

// 상품명 생성 함수
function getProductName(formData) {
    const printType = formData.printType || '흑백';
    const printMethod = formData.printMethod || 'single';
    const bindingType = formData.bindingType || '무선';
    
    // 한글 표기 맵핑
    const typeKo = {
        '흑백': '흑백',
        'black_white': '흑백',
        '잉크칼라': '잉크 칼라',
        'ink_color': '잉크 칼라',
        '레이져칼라': '레이저 칼라',
        'laser_color': '레이저 칼라'
    }[printType] || printType;
    
    const bindingKo = {
        '무선': '무선',
        'ring': '링',
        'perfect': '무선',
        'saddle': '중철'
    }[bindingType] || bindingType;
    
    let methodText = '단면';
    if (printMethod === 'double') {
        methodText = '양면';
    }
    
    return `${typeKo} ${methodText} ${bindingKo}제본`;
}

// 텍스트 미리보기 모달 표시 (온누리인쇄나라 견적서 양식)
// 견적서 미리보기 함수 (깔끔한 버전)
function showTextPreview(priceInfo) {
    console.log('미리보기 priceInfo 데이터:', priceInfo);
    
    const formData = {
        customerName: document.getElementById('customerName').value,
        email: document.getElementById('email') ? document.getElementById('email').value : '',
        pages: parseInt(document.getElementById('pages').value),
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: parseInt(document.getElementById('quantity').value)
    };

    // 새로운 깔끔한 모달 HTML
    const modalHtml = `
    <div class="modal fade" id="previewModal" tabindex="-1" aria-labelledby="previewModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="previewModalLabel">
                        <i class="fas fa-eye me-2"></i>견적서 미리보기
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body" style="padding: 20px; background: #f8f9fa;">
                    <div class="page a4" style="width: 100%; max-width: 900px; margin: 0 auto; font-family: 'Malgun Gothic', 'Noto Sans CJK KR', Arial, sans-serif; color: #000; padding: 0; display: block;">
                        <!-- 견적서 상자 -->
                        <div style="border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                            <!-- 상단: 견적서 제목 -->
                            <h1 style="color: #155724; font-size: 28px; font-weight: bold; text-align: center; margin-bottom: 30px;">
                                견적서
                            </h1>
                            
                            <!-- 상단 정보 영역 (세로 확대, 크기 동일, 폰트 더 작게) -->
                            <div style="display: flex; margin-bottom: 25px; gap: 20px; align-items: stretch; height: 180px; width: 100%;">
                                <!-- 좌측: 수신인 정보 (세로 확대) -->
                                <div style="flex: 1; text-align: left; padding: 15px; border: 1px solid #ddd; border-radius: 6px; display: flex; flex-direction: column; justify-content: space-between;">
                                    <div>
                                        <div style="margin-bottom: 15px; font-size: 14px; font-weight: bold; color: #333;">수신인</div>
                                        <div style="margin-bottom: 12px; font-size: 12px;">
                                            <strong>수신 :</strong> ${formData.customerName || '12'} 귀하
                                        </div>
                                        <div style="margin-bottom: 15px; font-size: 12px;">
                                            <strong>견적일자 :</strong> ${new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}
                                        </div>
                                    </div>
                                    <div style="font-size: 11px; font-style: italic; color: #666; text-align: center;">
                                        아래와 같이 견적합니다.
                                    </div>
                                </div>
                                
                                <!-- 우측: 공급자 정보 (세로 확대, 크기 동일, 폰트 더 작게) -->
                                <div style="flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; display: flex; flex-direction: column; align-items: stretch; justify-content: center; overflow: hidden;">
                                    <!-- 상단 라벨 -->
                                    <div style="background: #e9ecef; padding: 6px; text-align: center; font-weight: bold; font-size: 12px; color: #333; border-radius: 5px 5px 0 0; margin-bottom: 0;">
                                        공급자
                                    </div>
                                    
                                    <!-- 하단 테이블 (세로 확대, 폰트 더 작게) -->
                                    <div style="flex: 1; background: #f8f9fa; border-radius: 0 0 5px 5px; padding: 8px; overflow: hidden;">
                                        <table style="width: 100%; height: 100%; border-collapse: collapse; font-size: 6px; table-layout: fixed;">
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold; width: 20%;">상호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">온누리인쇄나라</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold; width: 20%;">대표자</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;">류도현</td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">사업자번호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">491-20-00640</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;"></td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;"></td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">주소</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;" colspan="3">서울 금천구 가산디지털1로 142 가산더스카이밸리1차 3층 816호</td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">업태</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">제조, 소매, 서비스업</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">종목</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;">경인쇄, 문구, 출력, 복사, 제본</td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">사업자계좌번호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">신한 110-493-223413</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">전화번호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;">02-6338-7123</td>
                                            </tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 합계금액 (총비용 + 세액) -->
                            <div style="margin-bottom: 80px; margin-top: 40px; padding: 15px; background: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; text-align: center;">
                                <div style="font-size: 16px; font-weight: bold; color: #1976d2;">
                                    합계금액: 일금 ${(priceInfo.total_price + (priceInfo.tax_amount || Math.round(priceInfo.total_price * 0.1))).toLocaleString()}원정
                                </div>
                            </div>
                            
                            
                            <!-- 견적 내용 테이블 (간격 더 확대) -->
                            <div style="margin-bottom: 120px; margin-top: 30px;">
                                <div style="font-size: 12px; font-weight: bold; color: #333; margin-bottom: 8px;">견적 내용</div>
                                <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; border-radius: 5px; overflow: hidden;">
                                    <thead>
                                        <tr style="background: #f8f9fa;">
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 20%; text-align: center;">상품명</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 12%; text-align: center;">규격</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 12%; text-align: center;">수량</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 18%; text-align: center;">부당 단가(부가세 제외)</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 18%; text-align: center;">총비용(부가세 제외)</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 20%; text-align: center;">세액</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${getProductName(formData)}</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${formData.size || 'A4'}</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${parseInt(formData.quantity).toLocaleString()}권</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${priceInfo.unit_price.toLocaleString()}원</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${priceInfo.total_price.toLocaleString()}원</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${priceInfo.tax_amount ? priceInfo.tax_amount.toLocaleString() : Math.round(priceInfo.total_price * 0.1).toLocaleString()}원</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <!-- 하단 서명 (간격 더 확대) -->
                            <div style="margin-top: 60px; padding: 25px; border: 1px solid #ddd; border-radius: 6px; text-align: right;">
                                <div style="margin-bottom: 10px; font-size: 14px; color: #333; font-weight: bold;">${new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
                                <div style="margin-bottom: 10px; font-size: 14px; color: #333; font-weight: bold;">온누리인쇄나라</div>
                                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
                                    <span style="font-size: 14px; color: #333; font-weight: bold;">류도현</span>
                                    <img src="static/images/도장.png" alt="도장" style="width: 35px; height: 35px;" onerror="this.style.display='none';">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fas fa-times me-2"></i>닫기
                    </button>
                    <button type="button" class="btn btn-primary" onclick="printPreview()">
                        <i class="fas fa-print me-2"></i>인쇄 (PDF 저장)
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('previewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
}

// 간단한 인쇄 함수 (브라우저 기본 인쇄 기능 사용)
// PDF 다운로드 함수 (간단하고 확실한 방법)
function printPreview() {
    const modal = document.getElementById('previewModal');
    const modalBody = modal.querySelector('.modal-body');
    
    if (!modalBody) {
        showAlert('미리보기 데이터를 찾을 수 없습니다.', 'danger');
        return;
    }
    
    // 저장 안내 메시지
    const saveMessage = `
        📁 PDF 저장 안내
        
        인쇄 대화상자가 열리면:
        1. "대상"을 "PDF로 저장" 선택
        2. 파일명을 "견적서_${new Date().toISOString().slice(0,10)}.pdf"로 설정
        3. 저장 버튼 클릭
        
        💡 이 방법이 가장 확실합니다!
    `;
    
    // 안내 메시지 표시
    showAlert(saveMessage, 'info');
    
    // 2초 후 인쇄 창 열기
    setTimeout(() => {
        // 새 창 열기
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        
        // 인쇄용 HTML 생성
        const printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>견적서</title>
                <style>
                    @page {
                        size: A4 portrait;
                        margin: 15mm;
                    }
                    body {
                        font-family: 'Malgun Gothic', 'Noto Sans CJK KR', Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        font-size: 12px;
                        line-height: 1.4;
                        background: white;
                        color: #000;
                    }
                    .page {
                        width: 100%;
                        max-width: 180mm;
                        margin: 0 auto;
                        background: white;
                        padding: 0;
                    }
                    @media print {
                        body {
                            -webkit-print-color-adjust: exact;
                            print-color-adjust: exact;
                        }
                        .page {
                            max-width: none;
                            width: 100%;
                        }
                        table {
                            page-break-inside: avoid;
                        }
                        .no-print {
                            display: none !important;
                        }
                    }
                    @media screen {
                        body {
                            padding: 20px;
                        }
                    }
                </style>
            </head>
            <body>
                ${modalBody.innerHTML}
            </body>
            </html>
        `;
        
        printWindow.document.write(printContent);
        printWindow.document.close();
        
        // 인쇄 대화상자 열기
        printWindow.onload = function() {
            setTimeout(function() {
                printWindow.print();
                // 3초 후 창 닫기
                setTimeout(function() {
                    printWindow.close();
                }, 3000);
            }, 1000);
        };
    }, 2000);
}

// 숫자를 한글로 변환하는 함수
function convertNumberToKorean(number) {
    if (number == 0) return '영';
    
    const units = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'];
    const tens = ['', '십', '백', '천'];
    const bigUnits = ['', '만', '억', '조'];
    
    const numStr = number.toString().split('').reverse().join('');
    const result = [];
    
    for (let i = 0; i < numStr.length; i++) {
        const digit = numStr[i];
        if (digit === '0') continue;
        
        if (i % 4 === 0 && i > 0) {
            const bigUnitIdx = Math.floor(i / 4);
            if (bigUnitIdx < bigUnits.length) {
                result.push(bigUnits[bigUnitIdx]);
            }
        }
        
        const smallUnitIdx = i % 4;
        if (smallUnitIdx > 0 && digit !== '1') {
            result.push(tens[smallUnitIdx]);
        } else if (smallUnitIdx > 0 && digit === '1') {
            result.push(tens[smallUnitIdx]);
        }
        
        if (digit !== '1' || smallUnitIdx === 0) {
            result.push(units[parseInt(digit)]);
        }
    }
    
    return result.reverse().join('');
}

// 스크롤 애니메이션 초기화
function initScrollAnimations() {
    const elements = document.querySelectorAll('.fade-in');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

// 부드러운 스크롤 초기화
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 알림 표시
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

// 전화번호 클릭 시 전화 걸기
function makeCall(phoneNumber) {
    window.location.href = `tel:${phoneNumber}`;
}

// 네이버블로그 열기
function openNaverBlog() {
    const blogUrl = 'https://blog.naver.com/onnuriinsenara';
    window.open(blogUrl, '_blank');
}

// 실시간 견적 미리보기
function updateQuotePreview() {
    const pages = parseInt(document.getElementById('pages').value) || 0;
    const printType = document.getElementById('printType').value;
    const quantity = parseInt(document.getElementById('quantity').value) || 0;
    
    if (pages > 0 && quantity > 0) {
        // 간단한 미리보기 계산
        const basePrices = {
            'black_white': 50,
            'ink_color': 200,
            'laser_color': 300
        };
        
        const unitPrice = basePrices[printType] * pages;
        const totalPrice = unitPrice * quantity;
        
        // 미리보기 표시 (선택사항)
        console.log(`예상 가격: ${totalPrice.toLocaleString()}원`);
    }
}

// 폼 유효성 검사
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// 숫자 입력 포맷팅
function formatNumber(input) {
    const value = input.value.replace(/[^0-9]/g, '');
    input.value = value;
}

// 페이지 로드 완료 후 실행
window.addEventListener('load', function() {
    // 초기화 작업
    console.log('온누리인쇄나라 웹사이트가 로드되었습니다.');
    
    // 애니메이션 시작
    document.body.classList.add('loaded');
    
    // 작업 사진 갤러리 초기화
    initPhotoGallery();
});

// 관리자 권한 확인
function checkAdminStatus() {
    // 간단한 관리자 확인 (실제로는 서버에서 세션 확인 필요)
    return localStorage.getItem('isAdmin') === 'true';
}

// 관리자 로그인 함수 (임시)
function adminLogin() {
    const password = prompt('관리자 비밀번호를 입력하세요:');
    if (password === 'admin123') { // 실제로는 서버 인증 필요
        localStorage.setItem('isAdmin', 'true');
        showAlert('관리자로 로그인되었습니다.', 'success');
        initPhotoGallery(); // 갤러리 다시 초기화
    } else if (password !== null) {
        showAlert('비밀번호가 올바르지 않습니다.', 'danger');
    }
}

// 관리자 로그아웃 함수
function adminLogout() {
    localStorage.removeItem('isAdmin');
    showAlert('관리자에서 로그아웃되었습니다.', 'info');
    initPhotoGallery(); // 갤러리 다시 초기화
}

// 작업 사진 갤러리 관련 함수들
function initPhotoGallery() {
    const photoUploadForm = document.getElementById('photoUploadForm');
    const folderButtons = document.querySelectorAll('[data-folder]');
    const uploadSection = document.getElementById('uploadSection');
    const folderSection = document.getElementById('folderSection');
    const adminLoginBtn = document.getElementById('adminLoginBtn');
    const folderForm = document.getElementById('folderForm');
    
    // 관리자 권한에 따라 업로드 섹션과 로그인 버튼 표시/숨김
    if (checkAdminStatus()) {
        if (uploadSection) {
            uploadSection.style.display = 'block';
        }
        if (folderSection) {
            folderSection.style.display = 'block';
        }
        if (adminLoginBtn) {
            adminLoginBtn.style.display = 'none';
        }
        if (photoUploadForm) {
            photoUploadForm.addEventListener('submit', handlePhotoUpload);
        }
        if (folderForm) {
            folderForm.addEventListener('submit', handleFolderCreate);
        }
    } else {
        if (uploadSection) {
            uploadSection.style.display = 'none';
        }
        if (folderSection) {
            folderSection.style.display = 'none';
        }
        if (adminLoginBtn) {
            adminLoginBtn.style.display = 'inline-block';
        }
    }
    
    if (folderButtons.length > 0) {
        folderButtons.forEach(button => {
            button.addEventListener('click', handleFolderFilter);
        });
    }
    
    // 초기 폴더와 사진 로드
    loadFolders();
    loadPhotos();
}

// 사진 업로드 처리
function handlePhotoUpload(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const photoFile = document.getElementById('photoFile').files[0];
    const folderId = document.getElementById('photoFolder').value;
    const description = document.getElementById('photoDescription').value;
    
    if (!photoFile) {
        showAlert('사진 파일을 선택해주세요.', 'warning');
        return;
    }
    
    if (!folderId) {
        showAlert('폴더를 선택해주세요.', 'warning');
        return;
    }
    
    formData.append('photo', photoFile);
    formData.append('folder_id', folderId);
    formData.append('description', description);
    
    // 업로드 버튼 비활성화
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>업로드 중...';
    
    fetch('/api/photos', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            // 폼 리셋
            e.target.reset();
            // 사진 목록 새로고침
            loadPhotos();
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('업로드 오류:', error);
        showAlert('업로드 중 오류가 발생했습니다.', 'danger');
    })
    .finally(() => {
        // 업로드 버튼 활성화
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

// 사진 목록 로드
function loadPhotos(category = 'all') {
    fetch('/api/photos')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayPhotos(data.photos, category);
        } else {
            console.error('사진 로드 오류:', data.error);
        }
    })
    .catch(error => {
        console.error('사진 로드 오류:', error);
    });
}

// 사진 표시
function displayPhotos(photos, folderId = 'all') {
    const gallery = document.getElementById('photoGallery');
    
    if (!gallery) return;
    
    // 필터링
    let filteredPhotos = photos;
    if (folderId !== 'all') {
        filteredPhotos = photos.filter(photo => photo.folder_id === folderId);
    }
    
    if (filteredPhotos.length === 0) {
        gallery.innerHTML = `
            <div class="col-12 text-center">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    ${folderId === 'all' ? '아직 업로드된 작업 사진이 없습니다.' : '해당 폴더의 사진이 없습니다.'}
                </div>
            </div>
        `;
        return;
    }
    
    // 사진 그리드 생성
    gallery.innerHTML = filteredPhotos.map(photo => `
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card h-100 border-0 shadow-sm">
                <div class="position-relative">
                    <img src="/uploads/${photo.filename}" class="card-img-top" alt="${photo.original_name}" style="height: 250px; object-fit: cover;">
                    <div class="position-absolute top-0 end-0 m-2">
                        <span class="badge bg-primary">${getFolderName(photo.folder_id)}</span>
                    </div>
                </div>
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title">${photo.original_name}</h6>
                    ${photo.description ? `<p class="card-text text-muted small">${photo.description}</p>` : ''}
                    <div class="mt-auto">
                        <small class="text-muted">
                            <i class="fas fa-calendar me-1"></i>
                            ${new Date(photo.upload_date).toLocaleDateString('ko-KR')}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// 폴더 필터 처리
function handleFolderFilter(e) {
    const folderId = e.target.getAttribute('data-folder');
    
    // 버튼 활성화 상태 변경
    document.querySelectorAll('[data-folder]').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    
    // 사진 필터링
    loadPhotos(folderId);
}

// 폴더명 변환
function getFolderName(folderId) {
    // 폴더 목록에서 이름 찾기
    const folders = window.folders || [];
    const folder = folders.find(f => f.id === folderId);
    return folder ? folder.name : folderId;
}

// 사진 삭제 (관리자용)
function deletePhoto(photoId) {
    if (!confirm('정말로 이 사진을 삭제하시겠습니까?')) {
        return;
    }
    
    fetch(`/api/photos/${photoId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            loadPhotos();
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('삭제 오류:', error);
        showAlert('삭제 중 오류가 발생했습니다.', 'danger');
    });
}

// 네이버 지도 열기
function openNaverMap() {
    window.open('https://map.naver.com/v5/search/온누리인쇄나라', '_blank');
}

// 폴더 관리 함수들
function loadFolders() {
    fetch('/api/folders')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.folders = data.folders;
            displayFolders(data.folders);
            updateFolderSelect(data.folders);
        } else {
            console.error('폴더 로드 오류:', data.error);
        }
    })
    .catch(error => {
        console.error('폴더 로드 오류:', error);
    });
}

function displayFolders(folders) {
    const folderList = document.getElementById('folderList');
    const folderFilter = document.querySelector('.folder-filter');
    
    if (!folderList || !folderFilter) return;
    
    // 폴더 목록 표시
    folderList.innerHTML = folders.map(folder => `
        <div class="folder-item d-flex justify-content-between align-items-center">
            <div>
                <div class="folder-name">${folder.name}</div>
                <div class="folder-description">${folder.description || '설명 없음'}</div>
            </div>
            <div>
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="deleteFolder('${folder.id}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    // 폴더 필터 버튼 업데이트
    const filterButtons = folders.map(folder => `
        <button type="button" class="btn btn-outline-primary" data-folder="${folder.id}">
            ${folder.name}
        </button>
    `).join('');
    
    folderFilter.innerHTML = `
        <button type="button" class="btn btn-outline-primary active" data-folder="all">
            전체
        </button>
        ${filterButtons}
    `;
    
    // 새 버튼들에 이벤트 리스너 추가
    folderFilter.querySelectorAll('[data-folder]').forEach(button => {
        button.addEventListener('click', handleFolderFilter);
    });
}

function updateFolderSelect(folders) {
    const folderSelect = document.getElementById('photoFolder');
    if (!folderSelect) return;
    
    folderSelect.innerHTML = '<option value="">폴더를 선택하세요</option>' +
        folders.map(folder => `<option value="${folder.id}">${folder.name}</option>`).join('');
}

function showCreateFolderForm() {
    document.getElementById('createFolderForm').style.display = 'block';
}

function hideCreateFolderForm() {
    document.getElementById('createFolderForm').style.display = 'none';
    document.getElementById('folderForm').reset();
}

function handleFolderCreate(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('folderName').value,
        description: document.getElementById('folderDescription').value
    };
    
    fetch('/api/folders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            hideCreateFolderForm();
            loadFolders();
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('폴더 생성 오류:', error);
        showAlert('폴더 생성 중 오류가 발생했습니다.', 'danger');
    });
}

function deleteFolder(folderId) {
    if (!confirm('정말로 이 폴더를 삭제하시겠습니까?')) {
        return;
    }
    
    fetch(`/api/folders/${folderId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            loadFolders();
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('폴더 삭제 오류:', error);
        showAlert('폴더 삭제 중 오류가 발생했습니다.', 'danger');
    });
}