from app import create_app

app = create_app()

from app.routes import bp

app.register_blueprint(bp)

app.run(debug=True, host='0.0.0.0', port=8000)
