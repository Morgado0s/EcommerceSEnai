// Funcionalidades JavaScript para o E-commerce

// Auto-hide flash messages
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(function(message) {
        // Auto hide after 5 seconds
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.style.display = 'none';
            }, 300);
        }, 5000);
    });
});

// Smooth scroll para links internos
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Confirmação para ações de delete
function confirmDelete(message) {
    return confirm(message || 'Tem certeza que deseja deletar este item?');
}

// Atualizar contador do carrinho
function updateCartCount() {
    const cartItems = document.querySelectorAll('.cart-item');
    const cartCount = document.querySelector('.cart-count');
    
    if (cartCount) {
        const count = cartItems.length;
        cartCount.textContent = count;
        cartCount.style.display = count > 0 ? 'inline' : 'none';
    }
}

// Validação de formulários
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#ff4757';
            isValid = false;
        } else {
            field.style.borderColor = '#e9ecef';
        }
    });
    
    return isValid;
}

// Formatação de preço
function formatPrice(price) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(price);
}

// Loading state para botões
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
    } else {
        button.disabled = false;
        // Restaurar texto original (seria necessário armazenar antes)
    }
}

// Busca em tempo real (debounced)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Aplicar debounce na busca se existir
const searchInput = document.querySelector('.search-input');
if (searchInput) {
    const debouncedSearch = debounce(function() {
        // Auto-submit do formulário de busca após 500ms de inatividade
        const form = searchInput.closest('form');
        if (form) {
            form.submit();
        }
    }, 500);
    
    searchInput.addEventListener('input', debouncedSearch);
}

// Animações de entrada
function animateOnScroll() {
    const elements = document.querySelectorAll('.product-card, .cart-item, .stat-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Inicializar animações quando a página carregar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', animateOnScroll);
} else {
    animateOnScroll();
}

// Função para preview de imagem em formulários
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const preview = document.getElementById(previewId);
            if (preview) {
                preview.src = e.target.result;
            }
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Máscara para campos de preço
function maskPrice(input) {
    let value = input.value.replace(/\D/g, '');
    value = (value / 100).toFixed(2);
    input.value = value;
}

// Aplicar máscara em campos de preço
document.querySelectorAll('input[name="preco"]').forEach(input => {
    input.addEventListener('input', function() {
        // Permitir apenas números e ponto decimal
        this.value = this.value.replace(/[^0-9.]/g, '');
        
        // Garantir apenas um ponto decimal
        const parts = this.value.split('.');
        if (parts.length > 2) {
            this.value = parts[0] + '.' + parts.slice(1).join('');
        }
        
        // Limitar casas decimais
        if (parts[1] && parts[1].length > 2) {
            this.value = parts[0] + '.' + parts[1].substring(0, 2);
        }
    });
});

// Função para mostrar/esconder senha
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.nextElementSibling;
    
    if (input.type === 'password') {
        input.type = 'text';
        if (icon) icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        if (icon) icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

// Adicionar funcionalidade de busca instantânea
function setupInstantSearch() {
    const searchForm = document.querySelector('.filter-form');
    const searchInput = document.querySelector('.search-input');
    const categorySelect = document.querySelector('.category-select');
    
    if (searchForm && (searchInput || categorySelect)) {
        const performSearch = debounce(() => {
            searchForm.submit();
        }, 300);
        
        if (searchInput) {
            searchInput.addEventListener('input', performSearch);
        }
        
        if (categorySelect) {
            categorySelect.addEventListener('change', () => {
                searchForm.submit();
            });
        }
    }
}

// Inicializar busca instantânea
setupInstantSearch();

// Função para calcular total do carrinho em tempo real
function updateCartTotal() {
    const cartItems = document.querySelectorAll('.cart-item');
    let total = 0;
    
    cartItems.forEach(item => {
        const priceElement = item.querySelector('.total-price');
        if (priceElement) {
            const price = parseFloat(priceElement.textContent.replace('Total: R$ ', '').replace(',', '.'));
            if (!isNaN(price)) {
                total += price;
            }
        }
    });
    
    const totalElement = document.querySelector('.summary-total span:last-child');
    if (totalElement) {
        totalElement.textContent = formatPrice(total);
    }
}

// Inicializar cálculo do total
updateCartTotal();

console.log('E-commerce JavaScript carregado com sucesso!');