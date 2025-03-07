// Main JavaScript for Marketplace Project

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('nav ul');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('show');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        const isNavToggle = event.target.closest('.nav-toggle');
        const isNavMenu = event.target.closest('nav ul');
        
        if (!isNavToggle && !isNavMenu && navMenu.classList.contains('show')) {
            navMenu.classList.remove('show');
        }
    });
    
    // Product image preview on add/edit product page
    const fileInput = document.getElementById('product-images');
    const imagePreview = document.querySelector('.image-preview');
    
    if (fileInput && imagePreview) {
        fileInput.addEventListener('change', function() {
            imagePreview.innerHTML = '';
            
            if (this.files) {
                for (let i = 0; i < this.files.length; i++) {
                    if (i >= 5) break; // Limit to 5 images
                    
                    const file = this.files[i];
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'preview-image';
                        imagePreview.appendChild(img);
                    }
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('form.needs-validation');
    
    if (forms.length > 0) {
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            }, false);
        });
    }
    
    // Product image gallery on product detail page
    const mainImage = document.getElementById('main-product-image');
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    
    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                mainImage.src = this.src;
                
                // Remove active class from all thumbnails
                thumbnails.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked thumbnail
                this.classList.add('active');
            });
        });
    }
    
    // Add to cart functionality
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    
    if (addToCartButtons.length > 0) {
        addToCartButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                
                const productId = this.dataset.productId;
                const productName = this.dataset.productName;
                
                // Show confirmation message
                alert(`เพิ่ม ${productName} ลงในตะกร้าเรียบร้อยแล้ว`);
                
                // Here you would typically send an AJAX request to add the item to cart
                console.log(`Product ${productId} added to cart`);
            });
        });
    }
    
    // Search functionality
    const searchForm = document.getElementById('search-form');
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(event) {
            const searchInput = document.getElementById('search-input');
            
            if (!searchInput.value.trim()) {
                event.preventDefault();
                alert('กรุณาใส่คำค้นหา');
            }
        });
    }
    
    // Image zoom on product detail page
    const zoomableImage = document.querySelector('.zoomable');
    
    if (zoomableImage) {
        zoomableImage.addEventListener('mousemove', function(e) {
            const x = e.clientX - this.offsetLeft;
            const y = e.clientY - this.offsetTop;
            
            const xPercent = x / this.offsetWidth * 100;
            const yPercent = y / this.offsetHeight * 100;
            
            this.style.transformOrigin = `${xPercent}% ${yPercent}%`;
        });
        
        zoomableImage.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.5)';
        });
        
        zoomableImage.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    }
    
    // Countdown for special offers
    const countdownElements = document.querySelectorAll('.countdown');
    
    if (countdownElements.length > 0) {
        countdownElements.forEach(element => {
            const endTime = new Date(element.dataset.endTime).getTime();
            
            const countdownInterval = setInterval(function() {
                const now = new Date().getTime();
                const distance = endTime - now;
                
                if (distance < 0) {
                    clearInterval(countdownInterval);
                    element.innerHTML = 'โปรโมชั่นสิ้นสุดแล้ว';
                    return;
                }
                
                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                
                element.innerHTML = `${days}วัน ${hours}ชั่วโมง ${minutes}นาที ${seconds}วินาที`;
            }, 1000);
        });
    }
});