from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run the app in debug mode so it auto-restarts when we make changes!
    app.run(debug=True, host= '0.0.0.0')