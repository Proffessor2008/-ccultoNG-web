class StegoProApp {
    constructor() {
        this.currentMethod = null;
        this.containerFile = null;
        this.dataFile = null;
        this.extractFile = null;
        this.stats = this.loadStats();
        this.achievements = this.loadAchievements();
        this.init();
    }
    init() {
        this.setupEventListeners();
        this.initializeAnimations();
        this.updateStats();
        this.checkAchievements();
        this.loadGoogleUser();
        this.loadTheme();
    }
    showHelp() {
        document.getElementById('helpModal').classList.remove('hidden');
    }
    hideHelp() {
        document.getElementById('helpModal').classList.add('hidden');
    }
    setupEventListeners() {
        // Navigation
        document.getElementById('startHiding').addEventListener('click', () => this.showHideInterface());
        document.getElementById('startExtracting').addEventListener('click', () => this.showExtractInterface());
        document.getElementById('userProfile').addEventListener('click', () => this.showProfile());
        document.getElementById('closeProfile').addEventListener('click', () => this.hideProfile());
        document.getElementById('googleLogoutBtn').addEventListener('click', () => {
            this.logoutGoogle();
        });
        // Method selection
        document.querySelectorAll('.method-card').forEach(card => {
            card.addEventListener('click', () => this.selectMethod(card.dataset.method));
        });
        document.getElementById('helpButton').addEventListener('click', () => this.showHelp());
        document.getElementById('closeHelp').addEventListener('click', () => this.hideHelp());
        // File handling
        this.setupFileHandling();
        // Password toggle
        document.getElementById('togglePassword').addEventListener('click', () => this.togglePassword('passwordInput'));
        document.getElementById('toggleExtractPassword').addEventListener('click', () => this.togglePassword('extractPassword'));
        // Actions
        document.getElementById('startHide').addEventListener('click', () => this.startHiding());
        document.getElementById('startExtract').addEventListener('click', () => this.startExtracting());
        document.getElementById('cancelHide').addEventListener('click', () => this.cancelOperation());
        document.getElementById('cancelExtract').addEventListener('click', () => this.cancelOperation());
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
        // Google login
        document.getElementById('googleLoginBtn').addEventListener('click', () => {
            window.location.href = '/auth/google';
        });
    }
    setupFileHandling() {
        // Container file
        const containerDropZone = document.getElementById('containerDropZone');
        const containerFileInput = document.getElementById('containerFile');
        document.getElementById('selectContainer').addEventListener('click', () => containerFileInput.click());
        containerFileInput.addEventListener('change', (e) => this.handleFileSelect(e, 'container'));
        this.setupDropZone(containerDropZone, 'container');

        // Data file
        const dataDropZone = document.getElementById('dataDropZone');
        const dataFileInput = document.getElementById('dataFile');
        document.getElementById('selectData').addEventListener('click', () => dataFileInput.click());
        dataFileInput.addEventListener('change', (e) => this.handleFileSelect(e, 'data'));
        this.setupDropZone(dataDropZone, 'data');

        // Extract file
        const extractDropZone = document.getElementById('extractDropZone');
        const extractFileInput = document.getElementById('extractFile');
        document.getElementById('selectExtractFile').addEventListener('click', () => extractFileInput.click());
        extractFileInput.addEventListener('change', (e) => this.handleFileSelect(e, 'extract'));
        this.setupDropZone(extractDropZone, 'extract');

        // Remove buttons
        document.getElementById('removeContainer').addEventListener('click', () => this.removeFile('container'));
        document.getElementById('removeData').addEventListener('click', () => this.removeFile('data'));
        document.getElementById('removeExtract').addEventListener('click', () => this.removeFile('extract'));
    }

    setupDropZone(element, type) {
        // Drag events
        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            element.classList.add('dragover');
        });
        element.addEventListener('dragleave', () => {
            element.classList.remove('dragover');
        });
        element.addEventListener('drop', (e) => {
            e.preventDefault();
            element.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.processFile(files[0], type);
            }
        });

        // CLICK on drop zone → open file input
        const inputMap = {
            container: 'containerFile',
            data: 'dataFile',
            extract: 'extractFile'
        };
        const fileInputId = inputMap[type];
        if (fileInputId) {
            element.addEventListener('click', (e) => {
                // Don't trigger if clicking on the "Select File" button
                if (e.target.closest('.btn-primary')) return;
                document.getElementById(fileInputId).click();
            });
        }
    }

    async loadGoogleUser() {
        try {
            const res = await fetch('/api/user');
            const user = await res.json();
            const navAvatar = document.getElementById('navAvatar');
            const navDefaultIcon = document.getElementById('navDefaultIcon');
            const avatar = document.getElementById('profileAvatar');
            const nameEl = document.getElementById('profileName');
            const emailEl = document.getElementById('profileEmail');
            const loginBtn = document.getElementById('googleLoginBtn');
            const logoutBtn = document.getElementById('googleLogoutBtn');

            if (user && user.logged_in) {
                // Обновляем аватар в навбаре
                if (user.picture) {
                    navAvatar.src = user.picture;
                    navAvatar.classList.remove('hidden');
                    navDefaultIcon.classList.add('hidden');
                } else {
                    navAvatar.classList.add('hidden');
                    navDefaultIcon.classList.remove('hidden');
                }

                // Обновляем аватар в модалке профиля
                if (user.picture) {
                    avatar.src = user.picture;
                    avatar.classList.remove('hidden');
                } else {
                    avatar.classList.add('hidden');
                }

                nameEl.textContent = user.name || 'Пользователь';
                emailEl.textContent = user.email || '';
                loginBtn.classList.add('hidden');
                logoutBtn.classList.remove('hidden');

                if (user.stats) {
                    this.stats = user.stats;
                    this.achievements = user.stats.achievements || [];
                    this.saveStats();
                    this.saveAchievements();
                    this.updateStats();
                }
            } else {
                // Сбрасываем аватар в навбаре
                navAvatar.classList.add('hidden');
                navDefaultIcon.classList.remove('hidden');

                // Сбрасываем модалку
                avatar.classList.add('hidden');
                nameEl.textContent = 'Пользователь';
                emailEl.textContent = '';
                loginBtn.classList.remove('hidden');
                logoutBtn.classList.add('hidden');
            }
        } catch (e) {
            console.error("Failed to load Google user", e);
            const loginBtn = document.getElementById('googleLoginBtn');
            const logoutBtn = document.getElementById('googleLogoutBtn');
            if (loginBtn) loginBtn.classList.remove('hidden');
            if (logoutBtn) logoutBtn.classList.add('hidden');

            // На всякий случай скрываем аватар и показываем иконку
            const navAvatar = document.getElementById('navAvatar');
            const navDefaultIcon = document.getElementById('navDefaultIcon');
            if (navAvatar) navAvatar.classList.add('hidden');
            if (navDefaultIcon) navDefaultIcon.classList.remove('hidden');
        }
    }

    handleFileSelect(event, type) {
        const file = event.target.files[0];
        if (file) {
            this.processFile(file, type);
        }
    }

    async logoutGoogle() {
        try {
            await fetch('/api/logout', { method: 'POST' });
        } catch (e) {
            console.error("Logout error", e);
        }
        this.stats = { filesProcessed: 0, dataHidden: 0, successfulOperations: 0 };
        this.achievements = [];
        this.saveStats();
        this.saveAchievements();
        this.updateStats();
        this.loadGoogleUser();
        this.showToast('Успешно', 'Вы вышли из аккаунта', 'success');
    }

    async saveStatsToCloud() {
        try {
            const response = await fetch('/api/save-stats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filesProcessed: this.stats.filesProcessed,
                    dataHidden: this.stats.dataHidden,
                    successfulOperations: this.stats.successfulOperations,
                    achievements: this.achievements
                })
            });
            if (response.ok) {
                console.log("Stats saved to cloud");
            }
        } catch (e) {
            console.error("Failed to save stats to cloud", e);
        }
    }

    processFile(file, type) {
        const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
        if (file.size > MAX_FILE_SIZE) {
            this.showToast('Ошибка', 'Файл слишком большой. Максимум 50 МБ.', 'error');
            return;
        }
        const validTypes = {
            container: ['.png', '.bmp', '.tiff', '.tif', '.wav'],
            data: null, // Any file
            extract: ['.png', '.bmp', '.tiff', '.tif', '.wav']
        };
        if (type !== 'data') {
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            if (!validTypes[type].includes(extension)) {
                this.showToast('Ошибка', `Неподдерживаемый формат файла. Разрешены: ${validTypes[type].join(', ')}`, 'error');
                return;
            }
        }
        if (type === 'container') {
            this.containerFile = file;
            this.showFileInfo(file, 'container');
        } else if (type === 'data') {
            this.dataFile = file;
            this.showFileInfo(file, 'data');
        } else if (type === 'extract') {
            this.extractFile = file;
            this.showFileInfo(file, 'extract');
        }
        this.updateActionButtons();
    }

    showFileInfo(file, type) {
        const infoElement = document.getElementById(type + 'Info');
        const nameElement = document.getElementById(type + 'Name');
        const sizeElement = document.getElementById(type + 'Size');
        nameElement.textContent = file.name;
        sizeElement.textContent = this.formatFileSize(file.size);
        infoElement.classList.remove('hidden');
        infoElement.classList.add('fade-in');
    }

    removeFile(type) {
        if (type === 'container') {
            this.containerFile = null;
            document.getElementById('containerInfo').classList.add('hidden');
            document.getElementById('containerFile').value = '';
        } else if (type === 'data') {
            this.dataFile = null;
            document.getElementById('dataInfo').classList.add('hidden');
            document.getElementById('dataFile').value = '';
        } else if (type === 'extract') {
            this.extractFile = null;
            document.getElementById('extractInfo').classList.add('hidden');
            document.getElementById('extractFile').value = '';
        }
        this.updateActionButtons();
    }

    updateActionButtons() {
        const hideButton = document.getElementById('startHide');
        const extractButton = document.getElementById('startExtract');
        if (this.currentMethod === 'lsb' || this.currentMethod === 'audio_lsb') {
            hideButton.disabled = !(this.containerFile && this.dataFile);
        }
        extractButton.disabled = !this.extractFile;
    }

    selectMethod(method) {
        this.currentMethod = method;
        document.querySelectorAll('.method-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.querySelector(`[data-method="${method}"]`).classList.add('selected');
        this.showHideInterface();
    }

    showHideInterface() {
        if (!this.currentMethod) {
            this.selectMethod('lsb');
        }
        document.getElementById('methodSelection').classList.add('hidden');
        document.getElementById('extractInterface').classList.add('hidden');
        document.getElementById('hideInterface').classList.remove('hidden');
        document.getElementById('hideInterface').classList.add('fade-in');
        this.updateActionButtons();
    }

    showExtractInterface() {
        document.getElementById('methodSelection').classList.add('hidden');
        document.getElementById('hideInterface').classList.add('hidden');
        document.getElementById('extractInterface').classList.remove('hidden');
        document.getElementById('extractInterface').classList.add('fade-in');
        this.updateActionButtons();
    }

    cancelOperation() {
        document.getElementById('hideInterface').classList.add('hidden');
        document.getElementById('extractInterface').classList.add('hidden');
        document.getElementById('methodSelection').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('hidden');
        this.containerFile = null;
        this.dataFile = null;
        this.extractFile = null;
        document.getElementById('containerInfo').classList.add('hidden');
        document.getElementById('dataInfo').classList.add('hidden');
        document.getElementById('extractInfo').classList.add('hidden');
        this.updateActionButtons();
    }

    async startHiding() {
        if (!this.containerFile || !this.dataFile || !this.currentMethod) {
            this.showToast('Ошибка', 'Не все необходимые файлы выбраны', 'error');
            return;
        }
        const password = document.getElementById('passwordInput').value;
        this.showProgress('hide');
        try {
            const result = await this.hideData(this.containerFile, this.dataFile, password);
            this.hideProgress();
            this.showResults('hide', result);
            this.updateStatsAfterOperation('hide', this.dataFile.size);
            this.checkAchievements();
        } catch (error) {
            this.hideProgress();
            this.showToast('Ошибка', 'Не удалось скрыть данные: ' + error.message, 'error');
        }
    }

    async startExtracting() {
        if (!this.extractFile) {
            this.showToast('Ошибка', 'Не выбран файл для извлечения', 'error');
            return;
        }
        const password = document.getElementById('extractPassword').value;
        this.showProgress('extract');
        try {
            const result = await this.extractData(this.extractFile, password);
            this.hideProgress();
            this.showResults('extract', result);
            this.updateStatsAfterOperation('extract');
            this.checkAchievements();
        } catch (error) {
            this.hideProgress();
            this.showToast('Ошибка', 'Не удалось извлечь данные: ' + error.message, 'error');
        }
    }

    async hideData(containerFile, dataFile, password) {
        const containerB64 = await this.fileToBase64(containerFile);
        const secretB64 = await this.fileToBase64(dataFile);
        const response = await fetch('/api/hide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                container: containerB64,
                secret: secretB64,
                method: this.currentMethod,
                password: password
            })
        });
        const result = await response.json();
        if (!result.success) throw new Error(result.error);
        return {
            success: true,
            method: result.method,
            stego_data: result.stego_data,
            file_extension: result.file_extension,
            originalSize: result.original_size,
            hiddenSize: result.hidden_size,
            stegoSize: result.stego_size
        };
    }

    async extractData(stegoFile, password) {
        const stegoB64 = await this.fileToBase64(stegoFile);
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stego: stegoB64, password: password })
        });
        const result = await response.json();
        if (!result.success) throw new Error(result.error);
        return {
            success: true,
            method: result.method,
            extracted_data: result.extracted_data,
            extractedSize: result.extracted_size,
            dataName: 'extracted_data.bin'
        };
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    showProgress(type) {
        const progressElement = document.getElementById(type + 'Progress');
        progressElement.classList.remove('hidden');
    }

    hideProgress() {
        document.getElementById('hideProgress').classList.add('hidden');
        document.getElementById('extractProgress').classList.add('hidden');
    }

    loadTheme() {
        const saved = localStorage.getItem('theme') || 'dark';
        const html = document.documentElement;
        const icon = document.getElementById('themeToggle').querySelector('i');
        if (saved === 'light') {
            html.classList.remove('dark');
            icon.className = 'fas fa-sun';
        } else {
            html.classList.add('dark');
            icon.className = 'fas fa-moon';
        }
    }

    showResults(operation, result) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');
        let html = '';
        if (operation === 'hide') {
            let stegoName = this.containerFile.name;
            if (result.file_extension) {
                const dotIndex = stegoName.lastIndexOf('.');
                if (dotIndex !== -1) {
                    stegoName = stegoName.substring(0, dotIndex) + '_stego' + result.file_extension;
                } else {
                    stegoName += '_stego' + result.file_extension;
                }
            } else {
                stegoName += '_stego';
            }
            const stegoUrl = 'data:application/octet-stream;base64,' + result.stego_data;
            html = `
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-check text-white text-2xl"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-green-400 mb-2">Данные успешно скрыты!</h3>
                    <p class="text-gray-400">Файл готов для скачивания</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div class="bg-gray-800 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">Информация</h4>
                        <p class="text-sm text-gray-400">Метод: <span class="text-blue-400">${(result.method || 'LSB').toUpperCase()}</span></p>
                        <p class="text-sm text-gray-400">Исходный размер: <span class="text-green-400">${this.formatFileSize(result.originalSize)}</span></p>
                        <p class="text-sm text-gray-400">Скрыто данных: <span class="text-yellow-400">${this.formatFileSize(result.hiddenSize)}</span></p>
                    </div>
                    <div class="bg-gray-800 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">Контейнер</h4>
                        <p class="text-sm text-gray-400">Имя: <span class="text-white">${stegoName}</span></p>
                        <p class="text-sm text-gray-400">Эффективность: <span class="text-purple-400">${Math.round((result.hiddenSize / result.originalSize) * 100)}%</span></p>
                    </div>
                </div>
                <div class="flex gap-4 justify-center">
                    <a href="${stegoUrl}" download="${stegoName}" class="btn-primary px-6 py-3 rounded-lg">
                        <i class="fas fa-download mr-2"></i>Скачать стего-файл
                    </a>
                    <button onclick="app.cancelOperation()" class="px-6 py-3 rounded-lg border border-gray-600 text-gray-300 hover:border-blue-500 hover:text-blue-500 transition-all">
                        Новая операция
                    </button>
                </div>
            `;
        } else if (operation === 'extract') {
            let dataName = 'extracted_data.bin';
            if (this.extractFile) {
                const baseName = this.extractFile.name.replace(/\.[^/.]+$/, "");
                dataName = baseName + '_extracted.bin';
            }
            const dataUrl = 'data:application/octet-stream;base64,' + result.extracted_data;
            html = `
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-unlock text-white text-2xl"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-blue-400 mb-2">Данные успешно извлечены!</h3>
                    <p class="text-gray-400">Скрытая информация восстановлена</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div class="bg-gray-800 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">Информация</h4>
                        <p class="text-sm text-gray-400">Метод: <span class="text-blue-400">${(result.method || 'Авто').toUpperCase()}</span></p>
                        <p class="text-sm text-gray-400">Извлечено: <span class="text-green-400">${this.formatFileSize(result.extractedSize)}</span></p>
                        <p class="text-sm text-gray-400">Целостность: <span class="text-green-400">Проверена</span></p>
                    </div>
                    <div class="bg-gray-800 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">Файл</h4>
                        <p class="text-sm text-gray-400">Имя: <span class="text-white">${dataName}</span></p>
                        <p class="text-sm text-gray-400">Статус: <span class="text-green-400">Готов</span></p>
                    </div>
                </div>
                <div class="flex gap-4 justify-center">
                    <a href="${dataUrl}" download="${dataName}" class="btn-primary px-6 py-3 rounded-lg">
                        <i class="fas fa-download mr-2"></i>Скачать данные
                    </a>
                    <button onclick="app.cancelOperation()" class="px-6 py-3 rounded-lg border border-gray-600 text-gray-300 hover:border-blue-500 hover:text-blue-500 transition-all">
                        Новая операция
                    </button>
                </div>
            `;
        }
        resultsContent.innerHTML = html;
        resultsSection.classList.remove('hidden');
        resultsSection.classList.add('fade-in');
    }

    togglePassword(inputId) {
        const input = document.getElementById(inputId);
        const icon = input.nextElementSibling.querySelector('i');
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    }

    showProfile() {
        document.getElementById('profileModal').classList.remove('hidden');
        this.updateProfileStats();
        this.loadGoogleUser();
    }

    hideProfile() {
        document.getElementById('profileModal').classList.add('hidden');
    }

    updateProfileStats() {
        document.getElementById('profileFilesProcessed').textContent = this.stats.filesProcessed;
        document.getElementById('profileDataHidden').textContent = this.formatFileSize(this.stats.dataHidden);
        document.getElementById('profileAchievements').textContent = this.achievements.length;
        const achievementsContainer = document.getElementById('recentAchievements');
        if (this.achievements.length > 0) {
            const recentAchievements = this.achievements.slice(-3);
            achievementsContainer.innerHTML = recentAchievements.map(achievement => `
                <div class="flex items-center p-2 bg-gray-800 rounded text-sm">
                    <i class="fas fa-trophy text-yellow-400 mr-2"></i>
                    <span>${achievement.name}</span>
                </div>
            `).join('');
        } else {
            achievementsContainer.innerHTML = '<p class="text-gray-400 text-sm">Нет достижений</p>';
        }
    }

    initializeAnimations() {
        new Typed('#typed-text', {
            strings: [
                'Скрывайте данные в изображениях',
                'Извлекайте скрытую информацию',
                'Защищайте конфиденциальные файлы',
                'Используйте продвинутую стеганографию'
            ],
            typeSpeed: 50,
            backSpeed: 30,
            backDelay: 2000,
            loop: true
        });
        anime({
            targets: '.stats-card',
            translateY: [50, 0],
            opacity: [0, 1],
            delay: anime.stagger(100),
            duration: 800,
            easing: 'easeOutExpo'
        });
    }

    updateStats() {
        document.getElementById('filesProcessed').textContent = this.stats.filesProcessed;
        document.getElementById('dataHidden').textContent = this.formatFileSize(this.stats.dataHidden);
        document.getElementById('achievementsCount').textContent = this.achievements.length;
        const successRate = this.stats.filesProcessed > 0 ?
            Math.round((this.stats.successfulOperations / this.stats.filesProcessed) * 100) : 100;
        document.getElementById('successRate').textContent = successRate + '%';
    }

    updateStatsAfterOperation(operation, dataSize = 0) {
        this.stats.filesProcessed++;
        if (operation === 'hide') {
            this.stats.dataHidden += dataSize;
            this.stats.successfulOperations++;
        } else if (operation === 'extract') {
            this.stats.successfulOperations++;
        }
        this.saveStats();
        this.updateStats();
        this.saveStatsToCloud();
    }

    checkAchievements() {
        const newAchievements = [];
        if (this.stats.filesProcessed === 1 && !this.hasAchievement('first_file')) {
            newAchievements.push({
                id: 'first_file',
                name: 'Первый шаг',
                description: 'Обработан первый файл'
            });
        }
        if (this.stats.dataHidden >= 1024 * 1024 && !this.hasAchievement('data_hider')) {
            newAchievements.push({
                id: 'data_hider',
                name: 'Скрыватель данных',
                description: 'Скрыто более 1MB данных'
            });
        }
        if (this.stats.filesProcessed >= 10 && !this.hasAchievement('professional')) {
            newAchievements.push({
                id: 'professional',
                name: 'Профессионал',
                description: 'Обработано 10 файлов'
            });
        }
        newAchievements.forEach(achievement => {
            this.achievements.push(achievement);
            this.showAchievement(achievement);
        });
        if (newAchievements.length > 0) {
            this.saveAchievements();
            this.saveStatsToCloud();
        }
    }

    hasAchievement(id) {
        return this.achievements.some(a => a.id === id);
    }

    showAchievement(achievement) {
        this.showToast('Достижение разблокировано!', `${achievement.name}: ${achievement.description}`, 'success');
    }

    showToast(title, message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastIcon = document.getElementById('toastIcon');
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');
        toastIcon.className = '';
        if (type === 'success') {
            toastIcon.classList.add('fas', 'fa-check-circle', 'text-green-400', 'text-xl', 'mr-3');
        } else if (type === 'error') {
            toastIcon.classList.add('fas', 'fa-exclamation-circle', 'text-red-400', 'text-xl', 'mr-3');
        } else if (type === 'warning') {
            toastIcon.classList.add('fas', 'fa-exclamation-triangle', 'text-yellow-400', 'text-xl', 'mr-3');
        }
        toastTitle.textContent = title;
        toastMessage.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    toggleTheme() {
        const html = document.documentElement;
        const isCurrentlyDark = html.classList.contains('dark');
        const willBeDark = !isCurrentlyDark;
        html.classList.toggle('dark', willBeDark);
        localStorage.setItem('theme', willBeDark ? 'dark' : 'light');
        const icon = document.querySelector('#themeToggle i');
        if (icon) {
            icon.className = willBeDark ? 'fas fa-moon' : 'fas fa-sun';
        }
        this.showToast('Успех', `Тема: ${willBeDark ? 'Темная' : 'Светлая'}`, 'success');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    loadStats() {
        const saved = localStorage.getItem('stegopro_stats');
        return saved ? JSON.parse(saved) : {
            filesProcessed: 0,
            dataHidden: 0,
            successfulOperations: 0
        };
    }

    saveStats() {
        localStorage.setItem('stegopro_stats', JSON.stringify(this.stats));
    }

    loadAchievements() {
        const saved = localStorage.getItem('stegopro_achievements');
        return saved ? JSON.parse(saved) : [];
    }

    saveAchievements() {
        localStorage.setItem('stegopro_achievements', JSON.stringify(this.achievements));
    }
}

const app = new StegoProApp();
