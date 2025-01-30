import json
import os

# Read the questions
with open('questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get unique CMS and sort them
unique_cms = sorted(set(q.get('CM', '') for q in data['questions'] if q.get('CM')), 
                    key=lambda x: (int(x.split()[1].split('.')[0]), int(x.split('.')[1])))
CMS = unique_cms + ['Tout']  # Add "All" CM at the end

# Base HTML template
def create_html_template(title, questions):
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title} - QCM Mathématiques 3D</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 0 auto; 
            padding: 20px; 
        }}
        .page {{
            max-width: 800px; 
            margin: 0 auto;
        }}
        nav {{ 
            background-color: #f4f4f4; 
            padding: 10px; 
            margin-bottom: 20px; 
        }}
        nav a {{ 
            margin-right: 10px; 
            text-decoration: none; 
            color: #333; 
        }}
        .question {{ 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin-bottom: 20px; 
        }}
        .options-container {{ 
            display: flex; 
            flex-direction: column; 
        }}
        .options-container label {{ 
            display: flex; 
            align-items: center; 
            margin-bottom: 10px; 
        }}
        .options-container input[type="radio"] {{ 
            margin-right: 10px; 
        }}
        .feedback {{ 
            margin: 10px 0; 
            padding: 10px; 
            border-radius: 5px; 
        }}
        .feedback.correct {{ 
            background-color: #dff0d8; 
            color: #3c763d; 
        }}
        .feedback.incorrect {{ 
            background-color: #f2dede; 
            color: #a94442; 
        }}
        #next-btn {{ 
            display: none; 
            margin-top: 10px; 
            padding: 8px 15px; 
        }}
        #validate-btn {{ 
            margin-top: 10px;
            padding: 8px 15px; 
        }}
        #progress-counter {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 15px;
            color: #666;
        }}
        #refresh-btn {{
            margin-top: 10px;
            padding: 8px 15px;
        }}

        /* Mobile-friendly text sizing */
        @media screen and (max-width: 600px) {{
            h1 {{ 
                font-size: 3.5rem; 
                margin-bottom: 20px;
            }}
            .options-container label {{ 
                font-size: 0.9rem; 
            }}
            #validate-btn, #next-btn, #refresh-btn {{
                font-size: 0.9rem;
                padding: 6px 12px;
            }}
        }}
    </style>
</head>
<body>
    <nav>
        <a href="index.html">Tout</a>
        {"".join(f'<a href="{CM.lower().replace(" ", "_")}.html">{CM}</a>' for CM in CMS[:-1])}
    </nav>

    <div class="page">
        <h1>{title}</h1>
        
        <div id="quiz-container">
            <div id="current-question">
                <div class="question-container"></div>
                <div class="feedback"></div>
                <button id="validate-btn">Valider</button>
                <button id="next-btn" style="display: none;">Suivant</button>
                <button id="refresh-btn" style="display: none;">Recommencer le Quiz</button>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function () {{
            const QUIZ_STATE_KEY = `qcm_state_${{document.title}}`;

            function saveQuizState() {{
                const quizState = {{
                    availableQuestions: availableQuestions,
                    answeredQuestions: answeredQuestions,
                    score: score,
                    totalQuestions: totalQuestions
                }};
                localStorage.setItem(QUIZ_STATE_KEY, JSON.stringify(quizState));
            }}

            function loadQuizState() {{
                const savedState = localStorage.getItem(QUIZ_STATE_KEY);
                if (savedState) {{
                    const parsedState = JSON.parse(savedState);
                    availableQuestions = parsedState.availableQuestions;
                    answeredQuestions = parsedState.answeredQuestions;
                    score = parsedState.score;
                    totalQuestions = parsedState.totalQuestions;
                    return true;
                }}
                return false;
            }}

            function resetQuizState() {{
                localStorage.removeItem(QUIZ_STATE_KEY);
                availableQuestions = [...allQuestions];
                answeredQuestions = 0;
                score = 0;
                totalQuestions = allQuestions.length;
                incorrectAttempts = [];
            }}

            function saveQuizCompletionState() {{
                localStorage.setItem(`${{QUIZ_STATE_KEY}}_completed`, 'true');
            }}

            function checkQuizCompletionState() {{
                return localStorage.getItem(`${{QUIZ_STATE_KEY}}_completed`) === 'true';
            }}

            function clearQuizCompletionState() {{
                localStorage.removeItem(`${{QUIZ_STATE_KEY}}_completed`);
            }}

            const allQuestions = {json.dumps(questions)};
            let availableQuestions = [];
            let answeredQuestions = 0;
            let score = 0;
            let totalQuestions = allQuestions.length;

            if (!loadQuizState()) {{
                availableQuestions = [...allQuestions];
            }}

            let currentQuestionIndex = 0;
            let answeredCorrectly = false;
            let incorrectAttempts = [];

            const currentQuestionEl = document.getElementById('current-question');
            const validateBtn = document.getElementById('validate-btn');
            const nextBtn = document.getElementById('next-btn');
            const refreshBtn = document.getElementById('refresh-btn');
            const progressCounter = document.createElement('div');
            progressCounter.id = 'progress-counter';
            currentQuestionEl.insertBefore(progressCounter, currentQuestionEl.firstChild);

            function shuffleOptions(options, correctValue) {{
                // Create a copy of the options to shuffle
                const shuffledOptions = [...options];
                
                // Find the index of the correct option
                const correctIndex = shuffledOptions.findIndex(opt => opt.value === correctValue);
                const correctOption = shuffledOptions[correctIndex];
                
                // Remove the correct option from the array
                shuffledOptions.splice(correctIndex, 1);
                
                // Shuffle the remaining options
                for (let i = shuffledOptions.length - 1; i > 0; i--) {{
                    const j = Math.floor(Math.random() * (i + 1));
                    [shuffledOptions[i], shuffledOptions[j]] = [shuffledOptions[j], shuffledOptions[i]];
                }}
                
                // Randomly insert the correct option
                const newCorrectIndex = Math.floor(Math.random() * (shuffledOptions.length + 1));
                shuffledOptions.splice(newCorrectIndex, 0, correctOption);
                
                return shuffledOptions;
            }}

            function updateProgressCounter() {{
                progressCounter.textContent = `Questions répondues : ${{answeredQuestions}} / ${{totalQuestions}}`;
                saveQuizState();
            }}

            function renderQuestion(index) {{
                const questionContainer = currentQuestionEl.querySelector('.question-container');
                const feedbackEl = currentQuestionEl.querySelector('.feedback');
                const currentQuestion = availableQuestions[index];

                // Shuffle options while preserving the correct answer
                const shuffledOptions = shuffleOptions(currentQuestion.options, currentQuestion.correct);

                // Clear previous question
                questionContainer.innerHTML = '';
                feedbackEl.innerHTML = '';
                feedbackEl.className = 'feedback';

                // Render question text
                const questionTextEl = document.createElement('p');
                questionTextEl.textContent = currentQuestion.text;
                questionContainer.appendChild(questionTextEl);

                // Render shuffled options
                const optionsContainer = document.createElement('div');
                optionsContainer.className = 'options-container';
                shuffledOptions.forEach((option, optionIndex) => {{
                    const label = document.createElement('label');
                    const radio = document.createElement('input');
                    radio.type = 'radio';
                    radio.name = 'answer';
                    radio.value = option.value;
                    radio.id = `option-${{optionIndex}}`;
                    
                    const labelText = document.createTextNode(option.text);
                    label.appendChild(radio);
                    label.appendChild(labelText);
                    optionsContainer.appendChild(label);
                }});
                questionContainer.appendChild(optionsContainer);

                // Reset buttons
                validateBtn.style.display = 'block';
                validateBtn.disabled = false;
                nextBtn.style.display = 'none';
                refreshBtn.style.display = 'none';
                answeredCorrectly = false;
                incorrectAttempts = [];
                updateProgressCounter();
            }}

            function clearRadioSelections() {{
                const radios = document.querySelectorAll('input[name="answer"]');
                radios.forEach(radio => radio.checked = false);
            }}

            function showRefreshButton() {{
                // Hide other buttons
                validateBtn.style.display = 'none';
                nextBtn.style.display = 'none';
                
                // Save completion state
                saveQuizCompletionState();
                
                // Show refresh button
                refreshBtn.style.display = 'block';
                
                // Update progress text to show completion
                progressCounter.textContent = `Toutes les questions ont été répondues ! Votre score : ${{score}} / ${{totalQuestions}}`;
            }}

            refreshBtn.addEventListener('click', function() {{
                // Reset the entire quiz state
                resetQuizState();
                
                // Clear completion state
                clearQuizCompletionState();
                
                // Hide refresh button
                refreshBtn.style.display = 'none';
                
                // Reinitialize the quiz
                availableQuestions = [...allQuestions];
                currentQuestionIndex = Math.floor(Math.random() * availableQuestions.length);
                renderQuestion(currentQuestionIndex);
                
                // Reset UI elements
                validateBtn.style.display = 'block';
                nextBtn.style.display = 'none';
                
                // Update progress counter
                updateProgressCounter();
            }});

            validateBtn.addEventListener('click', function() {{
                const selectedOption = document.querySelector('input[name="answer"]:checked');
                const feedbackEl = currentQuestionEl.querySelector('.feedback');
                const currentQuestion = availableQuestions[currentQuestionIndex];

                if (!selectedOption) {{
                    alert('Veuillez sélectionner une réponse');
                    return;
                }}

                const shuffledOptions = shuffleOptions(currentQuestion.options, currentQuestion.correct);
                const correctOption = shuffledOptions.find(option => option.value === currentQuestion.correct);

                if (selectedOption.value === correctOption.value) {{
                    // Correct answer
                    feedbackEl.textContent = `Correct ! ${{currentQuestion.explanation}}`;
                    feedbackEl.classList.remove('incorrect');
                    feedbackEl.classList.add('correct');
                    score++;
                    answeredCorrectly = true;
                    validateBtn.style.display = 'none';
                    nextBtn.style.display = 'block';
                    
                    // Remove current question from available questions
                    availableQuestions.splice(currentQuestionIndex, 1);
                    answeredQuestions++;

                    // If all questions answered, show refresh button
                    if (availableQuestions.length === 0) {{
                        showRefreshButton();
                    }}
                }} else {{
                    // Incorrect answer
                    if (!incorrectAttempts.includes(selectedOption.value)) {{
                        incorrectAttempts.push(selectedOption.value);
                        feedbackEl.textContent = `Incorrect. Réessayez !`;
                        feedbackEl.classList.remove('correct');
                        feedbackEl.classList.add('incorrect');
                    }} else {{
                        return;
                    }}
                }}

                // Save quiz state after each interaction
                saveQuizState();
            }});

            nextBtn.addEventListener('click', function() {{
                // If all questions have been answered, show refresh button
                if (availableQuestions.length === 0) {{
                    showRefreshButton();
                    return;
                }}

                // Randomly select next question
                currentQuestionIndex = Math.floor(Math.random() * availableQuestions.length);
                renderQuestion(currentQuestionIndex);
                saveQuizState();
            }});

            // Check for quiz completion state on page load
            if (checkQuizCompletionState()) {{
                // Restore the refresh button state
                validateBtn.style.display = 'none';
                nextBtn.style.display = 'none';
                refreshBtn.style.display = 'block';
                progressCounter.textContent = `Toutes les questions ont été répondues ! Votre score : ${{score}} / ${{totalQuestions}}`;
            }}

            // Initial render
            if (availableQuestions.length > 0) {{
                currentQuestionIndex = Math.floor(Math.random() * availableQuestions.length);
                renderQuestion(currentQuestionIndex);
            }}

            // Update progress counter on initial load
            updateProgressCounter();
        }});
    </script>
</body>
</html>'''

# Generate pages for each CM
for CM in CMS:
    if CM == 'Tout':
        filtered_questions = data['questions']
    else:
        filtered_questions = [q for q in data['questions'] if q.get('CM') == CM]
    
    filename = 'index.html' if CM == 'Tout' else f"{CM.lower().replace(' ', '_')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(create_html_template(CM, filtered_questions))

print("Pages generated successfully!")
