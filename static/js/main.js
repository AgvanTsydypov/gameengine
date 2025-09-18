// GlitchPeachAI - Pixel Theme JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Audio for pixel-style UI sounds (disabled)
    // const audioCtx = (window.AudioContext || window.webkitAudioContext) ? 
    //     new (window.AudioContext || window.webkitAudioContext)() : null;
    
    // function bleep(freq = 720, dur = 0.06) {
    //     if (!audioCtx) return;
    //     const o = audioCtx.createOscillator();
    //     const g = audioCtx.createGain();
    //     o.type = 'square';
    //     o.frequency.value = freq;
    //     g.gain.value = 0.02;
    //     o.connect(g);
    //     g.connect(audioCtx.destination);
    //     o.start();
    //     setTimeout(() => o.stop(), dur * 1000);
    // }

    // Add sound effects to buttons (disabled)
    // document.querySelectorAll('.btn').forEach(b => {
    //     b.addEventListener('click', () => bleep(520, 0.08), { passive: true });
    // });

    // Check if user is authenticated
    const isAuthenticated = document.body.dataset.authenticated === 'true';
    
    // Apply authentication state to UI
    function updateAuthState() {
        const authRequiredElements = document.querySelectorAll('.auth-required');
        authRequiredElements.forEach(el => {
            if (isAuthenticated) {
                el.classList.add('authenticated');
            } else {
                el.classList.remove('authenticated');
            }
        });
    }

    // Initialize authentication state
    updateAuthState();

    // Mobile menu toggle functionality
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            const isExpanded = mobileMenuToggle.getAttribute('aria-expanded') === 'true';
            
            // Toggle menu visibility
            if (isExpanded) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
            } else {
                mobileMenu.classList.add('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'true');
            }
            
            // Sound effect disabled
            // bleep(640, 0.06);
        });
        
        // Close mobile menu when clicking on a menu item
        mobileMenu.addEventListener('click', function(e) {
            if (e.target.closest('.btn')) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuToggle.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close mobile menu on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Publish and Update modals (keeping these for game creation/editing)
    const modals = {
        publish: document.getElementById('publish-modal'),
        update: document.getElementById('update-modal')
    };

    function clearModalData(modalId) {
        // Clear any existing global alerts
        const existingAlert = document.querySelector('.global-alert');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        if (modalId === 'publish') {
            // Clear publish form
            const publishForm = document.getElementById('publish-form');
            if (publishForm) {
                publishForm.reset();
            }
            
            // Clear any publish alerts
            const publishAlert = document.getElementById('publish-alert');
            if (publishAlert) {
                publishAlert.innerHTML = '';
            }
            
            // Reset publish button state
            const publishSubmitBtn = document.getElementById('publish-submit-btn');
            const publishText = document.getElementById('publish-text');
            const publishProgress = document.getElementById('publish-progress');
            if (publishSubmitBtn) {
                publishSubmitBtn.disabled = false;
                publishSubmitBtn.classList.remove('loading');
            }
            if (publishText) {
                publishText.textContent = '🚀 PUBLISH TO COMMUNITY';
            }
            if (publishProgress) {
                publishProgress.style.display = 'none';
            }
        } else if (modalId === 'update') {
            // Clear update form
            const updateForm = document.getElementById('update-form');
            if (updateForm) {
                updateForm.reset();
            }
            
            // Clear any update alerts
            const updateAlert = document.getElementById('update-alert');
            if (updateAlert) {
                updateAlert.innerHTML = '';
            }
            
            // Reset update button state
            const updateSubmitBtn = document.getElementById('update-submit-btn');
            const updateText = document.getElementById('update-text');
            const updateProgress = document.getElementById('update-progress');
            if (updateSubmitBtn) {
                updateSubmitBtn.disabled = false;
                updateSubmitBtn.classList.remove('loading');
            }
            if (updateText) {
                updateText.textContent = '💾 UPDATE GAME';
            }
            if (updateProgress) {
                updateProgress.style.display = 'none';
            }
        }
    }

    // Close modals with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (modals.publish && modals.publish.style.display === 'flex') {
                closePublishModal();
                clearModalData('publish');
            } else if (modals.update && modals.update.style.display === 'flex') {
                closeUpdateModal();
                clearModalData('update');
            }
        }
    });

    // Auth-required element click handlers
    document.querySelectorAll('.auth-required:not(.authenticated)').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            showAlert('Please log in to access this feature', 'error');
            window.location.href = '/login';
        });
    });

    // Alert system
    function showAlert(message, type = 'info', container = null) {
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type}`;
        alertEl.textContent = message;
        
        if (container) {
            container.innerHTML = '';
            container.appendChild(alertEl);
        } else {
            // Global alert
            const existingAlert = document.querySelector('.global-alert');
            if (existingAlert) {
                existingAlert.remove();
            }
            
            alertEl.classList.add('global-alert');
            alertEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 2000;
                max-width: 400px;
            `;
            document.body.appendChild(alertEl);
            
            setTimeout(() => {
                if (alertEl.parentNode) {
                    alertEl.remove();
                }
            }, 5000);
        }
    }

    // Form submission handlers for auth pages (now on separate pages)
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(loginForm);
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const alertContainer = document.getElementById('login-alert') || document.querySelector('.auth-body');
            
            // Loading state
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    // JSON response (AJAX)
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        // Success - redirect to home page or specified redirect
                        showAlert('Login successful!', 'success');
                        setTimeout(() => {
                            window.location.href = result.redirect || '/';
                        }, 500);
                    } else {
                        const errorMessage = result.error || 'Invalid email or password';
                        showAlert(errorMessage, 'error', alertContainer);
                    }
                } else {
                    // HTML response (fallback) - redirect to home page
                    window.location.href = '/';
                }
            } catch (error) {
                console.error('Login error:', error);
                showAlert('Login failed. Please try again.', 'error', alertContainer);
            } finally {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(registerForm);
            const password = formData.get('password');
            const confirmPassword = formData.get('confirm_password');
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            const alertContainer = document.getElementById('register-alert') || document.querySelector('.auth-body');
            
            // Validate passwords match
            if (password !== confirmPassword) {
                showAlert('Passwords do not match', 'error', alertContainer);
                return;
            }

            // Loading state
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;

            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    // JSON response (AJAX)
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        if (result.email_confirmation_required) {
                            // Show email verification alert
                            showAlert('Registration successful! Please check your email and click the confirmation link to complete your registration.', 'warning', alertContainer);
                            // Stay on register page to show the alert
                        } else {
                            showAlert('Account created successfully! Please log in.', 'success', alertContainer);
                            setTimeout(() => {
                                window.location.href = result.redirect || '/login';
                            }, 2000);
                        }
                    } else {
                        const errorMessage = result.error || 'Registration failed. Please try again.';
                        showAlert(errorMessage, 'error', alertContainer);
                    }
                } else {
                    // HTML response (fallback) - redirect to login page
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Registration error:', error);
                showAlert('Registration failed. Please try again.', 'error', alertContainer);
            } finally {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
        });
    }

    // Parallax starfield (no images) with pixel feel
    (() => {
        const canvas = document.getElementById('starfield');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d', { alpha: false });
        let w, h, dpr, stars = [], layers = 3;
        let mouseX = .5, mouseY = .5;
        const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        function resize() {
            dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
            w = Math.floor(innerWidth);
            h = Math.floor(innerHeight);
            canvas.width = w * dpr;
            canvas.height = h * dpr;
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            init();
        }

        function rnd(a, b) {
            return a + Math.random() * (b - a);
        }

        function init() {
            stars = [];
            const base = reduce ? 100 : 260;
            for (let z = 0; z < layers; z++) {
                const n = Math.floor(base * (z === 0 ? 0.5 : z === 1 ? 0.33 : 0.17));
                for (let i = 0; i < n; i++) {
                    stars.push({
                        x: Math.random() * w,
                        y: Math.random() * h,
                        z,
                        r: rnd(1, 2.2) + z * 0.6,
                        s: rnd(0.03, 0.09) * (1 + z * 0.6),
                        tw: Math.random() * Math.PI * 2
                    });
                }
            }
        }

        addEventListener('mousemove', e => {
            mouseX = e.clientX / w;
            mouseY = e.clientY / h;
        }, { passive: true });

        addEventListener('deviceorientation', e => {
            if (e.gamma != null && e.beta != null) {
                mouseX = Math.min(1, Math.max(0, (e.gamma + 45) / 90));
                mouseY = Math.min(1, Math.max(0, (e.beta + 45) / 90));
            }
        });

        function tick() {
            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
            ctx.fillRect(0, 0, w, h);
            
            // Add faint grid pixels
            ctx.globalAlpha = .08;
            ctx.fillStyle = '#0e1322';
            for (let gx = 0; gx < w; gx += 24) {
                ctx.fillRect(gx, 0, 1, h);
            }
            for (let gy = 0; gy < h; gy += 24) {
                ctx.fillRect(0, gy, w, 1);
            }
            ctx.globalAlpha = 1;

            for (const s of stars) {
                s.y += s.s;
                if (s.y > h + 2) s.y = -2;
                s.tw += 0.05 + s.z * 0.03;
                const a = 0.45 + Math.abs(Math.sin(s.tw)) * (0.4 + s.z * 0.1);
                const px = (mouseX - .5) * (7 + s.z * 12);
                const py = (mouseY - .5) * (7 + s.z * 12);
                
                // Draw square pixels instead of circles for an 8-bit feel
                const size = s.r;
                if (s.z === 0) ctx.fillStyle = `rgba(255,255,255,${a})`;
                else if (s.z === 1) ctx.fillStyle = `rgba(157,123,255,${a * 0.9})`;
                else ctx.fillStyle = `rgba(30,228,255,${a * 0.85})`;
                ctx.fillRect((s.x - px) | 0, (s.y - py) | 0, size, size);
            }
            if (!reduce) requestAnimationFrame(tick);
        }

        resize();
        addEventListener('resize', resize);
        if (reduce) {
            tick();
        } else {
            requestAnimationFrame(tick);
        }
    })();

    // Automatic alert dismissal
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    });

    // ============ LIKE SYSTEM FUNCTIONALITY ============
    
    // Like System Functionality
    function handleLikeAction(gameId, button) {
        // Prevent multiple clicks
        if (button.classList.contains('loading')) return;
        
        button.classList.add('loading');
        
        fetch('/toggle_like_game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ game_id: gameId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update all like buttons and displays for this game
                updateLikeUI(gameId, data.is_liked);
                // Removed success notification for like/unlike actions
            } else {
                showAlert(data.error || 'Failed to update like status', 'error');
            }
        })
        .catch(error => {
            console.error('Like error:', error);
            showAlert('Error updating like status', 'error');
        })
        .finally(() => {
            button.classList.remove('loading');
        });
    }

    function updateLikeUI(gameId, isLiked) {
        // Find all elements related to this game
        const likeBtns = document.querySelectorAll(`[data-game-id="${gameId}"]`);
        
        likeBtns.forEach(element => {
            const likeIcon = element.querySelector('.like-icon');
            const likeCount = element.querySelector('.like-count');
            const buttonText = element.querySelector('span');
            
            // Update like status
            if (isLiked) {
                element.classList.add('liked');
                if (likeIcon) likeIcon.textContent = '❤️';
                if (buttonText && element.classList.contains('like-btn-action')) {
                    buttonText.textContent = '💔 UNLIKE';
                }
            } else {
                element.classList.remove('liked');
                if (likeIcon) likeIcon.textContent = '🤍';
                if (buttonText && element.classList.contains('like-btn-action')) {
                    buttonText.textContent = '❤️ LIKE';
                }
            }
            
            // Update like count (approximate - we don't get the exact count back)
            if (likeCount) {
                const currentCount = parseInt(likeCount.textContent) || 0;
                const newCount = isLiked ? currentCount + 1 : Math.max(0, currentCount - 1);
                likeCount.textContent = newCount;
            }
        });
    }

    // Add click listeners to like buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.like-btn') || e.target.closest('.like-btn-action')) {
            e.preventDefault();
            e.stopPropagation();
            
            const button = e.target.closest('.like-btn') || e.target.closest('.like-btn-action');
            const gameId = button.getAttribute('data-game-id');
            
            if (gameId) {
                handleLikeAction(gameId, button);
            }
        }
    });
});

// Global utilities
window.App = {
    showAlert: function(message, type = 'info') {
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} global-alert`;
        alertEl.textContent = message;
        alertEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2000;
            max-width: 400px;
        `;
        
        const existingAlert = document.querySelector('.global-alert');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        document.body.appendChild(alertEl);
        
        setTimeout(() => {
            if (alertEl.parentNode) {
                alertEl.remove();
            }
        }, 5000);
    }
};

// Global functions for publish and update modals
window.closePublishModal = function() {
    const modal = document.getElementById('publish-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        // Clear modal data when closing
        if (typeof clearModalData === 'function') {
            clearModalData('publish');
        }
    }
};

window.closeUpdateModal = function() {
    const modal = document.getElementById('update-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        // Clear modal data when closing
        if (typeof clearModalData === 'function') {
            clearModalData('update');
        }
    }
};

// Override the existing functions to include clearing
window.publishGame = function() {
    if (!window.currentGameHtml) {
        App.showAlert('No game to publish. Please generate a game first.', 'error');
        return;
    }
    
    const title = document.getElementById('game-title-input').value.trim() || window.currentGameTitle;
    document.getElementById('publish-title').value = title;
    document.getElementById('publish-description').value = `AI-generated game: ${title}`;
    
    // Clear any existing data first
    if (typeof clearModalData === 'function') {
        clearModalData('publish');
    }
    
    // Then populate with new data
    document.getElementById('publish-title').value = title;
    document.getElementById('publish-description').value = `AI-generated game: ${title}`;
    
    // Ensure the form is properly populated
    setTimeout(() => {
        const modal = document.getElementById('publish-modal');
        modal.style.display = 'flex';
        modal.classList.add('show');
    }, 100);
};

window.updateGame = function() {
    if (!window.currentGameHtml) {
        App.showAlert('No game content to update.', 'error');
        return;
    }
    
    const title = document.getElementById('game-title-input').value.trim();
    const description = document.getElementById('game-description-input').value.trim();
    
    if (!title) {
        App.showAlert('Game title is required.', 'error');
        return;
    }
    
    // Clear any existing data first
    if (typeof clearModalData === 'function') {
        clearModalData('update');
    }
    
    // Then populate with new data
    document.getElementById('update-title').value = title;
    document.getElementById('update-description').value = description;
    
    // Show the update modal
    setTimeout(() => {
        const modal = document.getElementById('update-modal');
        modal.style.display = 'flex';
        modal.classList.add('show');
    }, 100);
};

// Add click outside handlers for publish and update modals
document.addEventListener('DOMContentLoaded', function() {
    // Publish modal click outside handler
    const publishModal = document.getElementById('publish-modal');
    if (publishModal) {
        publishModal.addEventListener('click', function(e) {
            if (e.target === publishModal) {
                closePublishModal();
            }
        });
    }
    
    // Update modal click outside handler
    const updateModal = document.getElementById('update-modal');
    if (updateModal) {
        updateModal.addEventListener('click', function(e) {
            if (e.target === updateModal) {
                closeUpdateModal();
            }
        });
    }
});