from app import create_app
#建立 Flask 主程式與 Mongo 連線
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
