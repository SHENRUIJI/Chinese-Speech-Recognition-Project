# Chinese-Speech-Recognition-Project
## Модельное обучение ( Шэнь Жуйцзи)
### `requirements.txt`: 

```text
torch==1.6.0
Levenshtein==0.12.0
librosa==0.8.0
warpctc_pytorch==0.2.1
tensorboardX==2.1
ctcdecode==1.0.2
pycorrector==0.3.0 #Chinese Text Error Corrector
sounddevice==0.4.1
pyaudio==0.2.11
Flask==1.1.2
Flask-Cors==3.0.9
tqdm==4.50.2
joblib==1.0.0
werkzeug==1.0.0
gunicorn==20.0.4
```
### 1. Предобработка данных

#### 1.1. `config.ipynb`: Этот файл является конфигурационным файлом, в котором хранятся пути к данным, модели и т.д.

#### 1.2. `data_preprocessing.py`: Этот скрипт читает данные и обрабатывает исходные данные, чтобы получить следующие три файла:

- `train.index`
- `dev.index`
- `labels.gz`

Файлы `train.index` и `dev.index` являются индексными файлами, которые представляют собой соответствие между аудиофайлами и их аннотациями.

Файл `labels.gz` является сжатым файлом, содержащим все символы, которые встречаются в аннотациях данных, представленных в виде списка.

#### 1.3. `processing_labels_gz.ipynb`: Этот файл предназначен для обработки labels.gz и удаления всех символов, кроме китайских.


