import os
from tqdm import tqdm
import pandas as pd
import logging
import joblib
from collections import ChainMap

# Настройка логирования / 配置日志记录
logging.basicConfig(filename='data_preprocessing.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Определение путей к директориям / 定义路径
current_dir = os.getcwd()

base_dir = current_dir 
train_path_dir = os.path.join(base_dir, 'data', 'train')
dev_path_dir = os.path.join(base_dir, 'data', 'dev')

logging.info(f"Base directory: {base_dir}")
logging.info(f"Train path directory: {train_path_dir}")
logging.info(f"Dev path directory: {dev_path_dir}")

# Получение путей к файлам для тренировочного и валидационного наборов данных / 获取训练集和开发集的文件路径
def get_files_paths(rootdir):
    files_paths = []
    for root, dirs, files in tqdm(os.walk(rootdir), desc=f"Searching in {rootdir}"):
        logging.info(f"Checking directory: {root}")  # 添加日志信息
        for file in files:
            if file.endswith('.wav'):
                wav_file = os.path.join(root, file)
                trn_file = os.path.join(root, file.replace('.wav', '.wav.trn'))
                logging.info(f"Found WAV file: {wav_file}, looking for TRN file: {trn_file}")  # 添加日志信息
                if os.path.exists(trn_file):
                    files_paths.append((wav_file, trn_file))
                    logging.info(f"Matched pair found: {wav_file} and {trn_file}")  # 添加日志信息
                else:
                    logging.warning(f"TRN file not found for WAV file: {wav_file}")  # 添加警告信息
    return files_paths

train_files_paths = get_files_paths(train_path_dir)
dev_files_paths = get_files_paths(dev_path_dir)

logging.info('train_files_paths len: %d', len(train_files_paths))
logging.info('dev_files_paths len: %d', len(dev_files_paths))

if not train_files_paths or not dev_files_paths:
    logging.error("No matching pairs found. Please check your data directory and file naming conventions.")
    exit(1)

# Чтение содержимого файла транскрипта и создание словаря / 读取transcript文件内容并创建字典
def read_trn(file_path):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
        if len(lines) >= 1:
            natural_text = lines[0].strip()
            pinyin_with_tones = lines[1].strip() if len(lines) > 1 else ''
            phonemes = lines[2].strip() if len(lines) > 2 else ''
            return natural_text, pinyin_with_tones, phonemes
    return None, None, None

# Создание индексных файлов для тренировочного и валидационного наборов данных / 创建训练集和开发集的索引文件
train_index = []
for wav_file, trn_file in tqdm(train_files_paths, desc="Processing train files"):
    natural_text, pinyin_with_tones, phonemes = read_trn(trn_file)
    if natural_text:
        train_index.append((wav_file, natural_text, pinyin_with_tones, phonemes))

dev_index = []
for wav_file, trn_file in tqdm(dev_files_paths, desc="Processing dev files"):
    natural_text, pinyin_with_tones, phonemes = read_trn(trn_file)
    if natural_text:
        dev_index.append((wav_file, natural_text, pinyin_with_tones, phonemes))

# Извлечение всех уникальных символов из текстов / 提取所有唯一字符
all_texts = [item[1] for item in train_index + dev_index]
all_characters = set(''.join(all_texts))

# Добавление пробела и подчеркивания в множество символов / 将空格和下划线添加到字符集中
all_characters = ['_'] + sorted(list(all_characters)) + [' ']

# Сохранение файла меток labels.gz / 保存 labels.gz 文件
output_dir = os.path.join(base_dir, 'processed/')
os.makedirs(output_dir, exist_ok=True)
labels_path = os.path.join(output_dir, 'labels.gz')
joblib.dump(all_characters, labels_path)
logging.info(f"Labels file saved to: {labels_path}")

# Создание индексных файлов / 创建索引文件
pd.DataFrame(train_index, columns=['file', 'natural_text', 'pinyin_with_tones', 'phonemes']).to_csv(
    os.path.join(output_dir, 'train.index'), index=False, header=True)
pd.DataFrame(dev_index, columns=['file', 'natural_text', 'pinyin_with_tones', 'phonemes']).to_csv(
    os.path.join(output_dir, 'dev.index'), index=False, header=True)

logging.info("Index files have been created successfully.")
