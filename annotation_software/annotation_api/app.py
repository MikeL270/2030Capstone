from app import create_app


app = create_app()

from app.routes import bp

app.register_blueprint(bp)



if __name__ == 'main':
    app.run(debug=True, host='0.0.0.0')
