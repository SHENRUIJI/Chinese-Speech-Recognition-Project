# 使用官方Python基础镜像，指定版本为3.10 Используйте официальный базовый образ Python, указав версию 3.10
FROM python:3.10-slim
 
# 更新包列表并安装系统依赖 Обновление списка пакетов и установка системных зависимостей
RUN apt-get update && \
    apt-get install -y libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 python3-all-dev libsndfile1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
 
# 设置工作目录 Настройка рабочего каталога
WORKDIR /app
 
# 将当前目录的内容复制到容器的/app目录中 Скопируйте содержимое текущего каталога в каталог /app контейнера
COPY . /app
 
# 安装gcc编译器以构建pyaudio的C扩展 Установка компилятора gcc для создания расширения pyaudio на языке C
RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*    
# 安装pyaudio（已经安装了系统依赖） Установите pyaudio (системные зависимости уже установлены)
RUN pip install pyaudio

# 安装Python依赖，包括torch, torchvision, and torchaudio Установите зависимости Python, включая torch, torchvision и torchaudio.
RUN pip install --no-cache-dir torch==2.3.0 torchvision torchaudio

# 安装git以克隆ctcdecode仓库 Установите git для клонирования репозитория ctcdecode
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# 安装g++编译器以编译ctcdecode的C++扩展 Установка компилятора g++ для компиляции расширений C++ для ctcdecode
RUN apt-get update && \
    apt-get install -y g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# 安装ctcdecode（需要先从GitHub克隆） Установите ctcdecode (сначала нужно сделать клон с GitHub).
RUN git clone --recursive https://github.com/WayenVan/ctcdecode.git && \
    cd ctcdecode && \
    pip install . && \
    cd .. && \
    rm -rf ctcdecode
 
# 安装其他Python依赖 Установите другие зависимости Python
RUN pip install --no-cache-dir -r requirements.txt
 
# 暴露应用运行的端口 Раскройте порт, на котором запущено приложение
EXPOSE 5000
 
# 运行应用
CMD ["python3", "masr_server.py"]
