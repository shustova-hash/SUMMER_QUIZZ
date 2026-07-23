let currentStep = 1;
let currentQuestionIndex = 0;
let userAnswers = [];
let registrationData = null;
let currentBranchSettings = {};

document.addEventListener('DOMContentLoaded', () => {
  loadBranchSettings();
  setupEventListeners();
});

async function loadBranchSettings() {
  try {
    const res = await fetch('/api/settings');
    if (res.ok) {
      currentBranchSettings = await res.json();
      renderBranchInfo();
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

function getYouTubeEmbedUrl(url) {
  if (!url) return null;
  url = String(url).trim();
  if (!url) return null;

  let fullUrl = url;
  if (!/^https?:\/\//i.test(fullUrl)) {
    fullUrl = 'https://' + fullUrl;
  }

  try {
    const regExp = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?|shorts)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/i;
    const match = fullUrl.match(regExp);
    if (match && match[1]) {
      return `https://www.youtube.com/embed/${match[1]}?autoplay=0&rel=0`;
    }

    if (/^[a-zA-Z0-9_-]{11}$/.test(url)) {
      return `https://www.youtube.com/embed/${url}?autoplay=0&rel=0`;
    }
  } catch (e) {
    console.error("Error parsing YouTube URL:", e);
  }
  return null;
}

function renderBranchInfo() {
  const branchNameEls = document.querySelectorAll('.dynamic-branch-name');
  branchNameEls.forEach(el => {
    el.textContent = currentBranchSettings.branch_name || 'Ковельська філія';
  });

  const phoneEls = document.querySelectorAll('.dynamic-phone');
  phoneEls.forEach(el => {
    if (currentBranchSettings.phone) {
      el.textContent = currentBranchSettings.phone;
      el.href = `tel:${currentBranchSettings.phone.replace(/[^\d+]/g, '')}`;
    }
  });

  const emailEls = document.querySelectorAll('.dynamic-email');
  emailEls.forEach(el => {
    if (currentBranchSettings.email) {
      el.textContent = currentBranchSettings.email;
      el.href = `mailto:${currentBranchSettings.email}`;
    }
  });

  const addressEls = document.querySelectorAll('.dynamic-address');
  addressEls.forEach(el => {
    if (currentBranchSettings.address) {
      el.textContent = currentBranchSettings.address;
    }
  });

  const ytUrl = currentBranchSettings.youtube_url || localStorage.getItem('youtube_url');
  const videoBox = document.querySelector('.video-box');
  if (videoBox && ytUrl) {
    const embedUrl = getYouTubeEmbedUrl(ytUrl);
    if (embedUrl) {
      videoBox.innerHTML = `
        <iframe 
          width="100%" 
          height="100%" 
          src="${embedUrl}" 
          title="Презентаційне відео ITSTEP" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen>
        </iframe>
      `;
    }
  }
}

function setupEventListeners() {
  // Screen 1 -> Screen 2
  const startRegBtn = document.getElementById('start-registration-btn');
  if (startRegBtn) {
    startRegBtn.addEventListener('click', () => showScreen(2));
  }

  // Screen 2 Registration Form Submit
  const regForm = document.getElementById('registration-form');
  if (regForm) {
    regForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = {
        child_name: document.getElementById('child_name').value.trim(),
        child_age: document.getElementById('child_age').value,
        city: document.getElementById('city').value,
        parent_name: document.getElementById('parent_name').value.trim(),
        parent_phone: document.getElementById('parent_phone').value.trim(),
        parent_email: document.getElementById('parent_email').value.trim()
      };

      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        const result = await res.json();
        if (res.ok && result.success) {
          registrationData = result;
          // Set name in screen 3
          document.getElementById('screen3-child-name').textContent = result.child_name;
          showScreen(3);
        } else {
          alert(result.error || 'Помилка при реєстрації. Перевірте введені дані.');
        }
      } catch (err) {
        alert('Помилка з\'єднання із сервером.');
      }
    });
  }

  // Screen 3 -> Screen 4 (Start Quiz)
  const startQuizBtn = document.getElementById('start-quiz-btn');
  if (startQuizBtn) {
    startQuizBtn.addEventListener('click', () => {
      currentQuestionIndex = 0;
      userAnswers = [];
      showScreen(4);
      renderQuestion();
    });
  }

  // Certificate Download Button
  const certBtn = document.getElementById('download-cert-btn');
  if (certBtn) {
    certBtn.addEventListener('click', () => {
      const childName = registrationData ? registrationData.child_name : 'Учасник';
      const branchName = currentBranchSettings.branch_name || 'Філія ITSTEP';
      const ticket = registrationData ? registrationData.ticket_number : 'ITS-000000';
      generateCertificate(childName, branchName, ticket);
    });
  }

  // Parent Guide Download Button
  const guideBtn = document.getElementById('download-guide-btn');
  if (guideBtn) {
    guideBtn.addEventListener('click', () => {
      window.location.href = '/api/files/download?type=parent_guide';
    });
  }
}

function showScreen(screenNum) {
  document.querySelectorAll('.screen-card').forEach(el => el.classList.add('hidden'));
  const targetScreen = document.getElementById(`screen-${screenNum}`);
  if (targetScreen) {
    targetScreen.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function renderQuestion() {
  const qData = QUIZ_QUESTIONS[currentQuestionIndex];
  if (!qData) {
    finishQuiz();
    return;
  }

  document.getElementById('quiz-step-indicator').textContent = `Запитання ${qData.id} з 10`;
  const progressPercent = (qData.id / 10) * 100;
  document.getElementById('quiz-progress-fill').style.width = `${progressPercent}%`;

  document.getElementById('quiz-question-title').textContent = qData.question;

  const optionsContainer = document.getElementById('quiz-options-container');
  optionsContainer.innerHTML = '';

  qData.options.forEach((opt) => {
    const card = document.createElement('div');
    card.className = 'quiz-option-card';
    card.innerHTML = `
      <span class="option-text">${opt.text}</span>
      <span class="option-tag">${opt.tag}</span>
    `;
    card.addEventListener('click', () => {
      userAnswers.push(opt.code);
      currentQuestionIndex++;
      if (currentQuestionIndex < QUIZ_QUESTIONS.length) {
        renderQuestion();
      } else {
        finishQuiz();
      }
    });
    optionsContainer.appendChild(card);
  });
}

async function finishQuiz() {
  const profile = calculateProfile(userAnswers);

  document.getElementById('result-badge').textContent = profile.badge;
  document.getElementById('result-title').textContent = profile.title;
  document.getElementById('result-icon').textContent = profile.icon;
  document.getElementById('result-parent-text').textContent = profile.parentText;

  if (registrationData) {
    document.getElementById('result-ticket-number').textContent = registrationData.ticket_number;
    // Update lead result profile in database
    try {
      await fetch('/api/update-result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_id: registrationData.lead_id,
          result_profile: profile.badge
        })
      });
    } catch (e) {
      console.error("Error updating result in DB", e);
    }
  }

  showScreen(5);
}
