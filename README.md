# Chinese-Speech-Recognition-Project
## Модельное обучение ( Шэнь Жуйцзи)

### 1. Предобработка данных

`data_preprocessing.py`: Этот скрипт читает данные и обрабатывает исходные данные, чтобы получить следующие три файла:

- `train.index`
- `dev.index`
- `labels.gz`

Файлы `train.index` и `dev.index` являются индексными файлами, которые представляют собой соответствие между аудиофайлами и их аннотациями.

Файл `labels.gz` является сжатым файлом, содержащим все символы, которые встречаются в аннотациях данных, представленных в виде списка.

`processing_labels_gz.ipynb`: Этот файл предназначен для обработки labels.gz и удаления всех символов, кроме китайских.
