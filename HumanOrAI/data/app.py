from flask import Flask, render_template, request, redirect, url_for
from services.model_service import ModelService

app = Flask(__name__)
model_service = ModelService()

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    input_text = ""
    selected_models = []

    if request.method == 'POST':
        # Formdan gelen verileri al
        input_text = request.form.get('text_input', '').strip()
        
        # Checkboxlardan seçilen modelleri al (Liste döner)
        selected_models = request.form.getlist('models')
        
        if input_text:
            result = model_service.predict(input_text, selected_models)

    # Sayfa ilk açıldığında hepsi seçili gelsin
    if not selected_models and request.method == 'GET':
        selected_models = ["Logistic Regression", "Naive Bayes", "Random Forest"]

    return render_template('index.html', 
                         result=result, 
                         input_text=input_text,
                         selected_models=selected_models)

# Sıfırlama Butonu için Route
@app.route('/reset')
def reset():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)