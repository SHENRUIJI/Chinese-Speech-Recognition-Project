from torch.utils.data import DataLoader, Dataset
import joblib
from feature import *
import os

# Помощная функция для проверки содержимого индексного файла
# 验证索引文件内容的辅助函数
def validate_index_file(index_path):
    with open(index_path) as f:
        idx = f.readlines()
    idx = [x.strip().split(",", 1) for x in idx]
    
    invalid_entries = []
    for i, (wav, _) in enumerate(idx):
        abs_wav = os.path.abspath(wav)
        trn_file = abs_wav + ".trn"
        if not os.path.exists(abs_wav) or not os.path.exists(trn_file):
            invalid_entries.append((i, abs_wav, trn_file))
    
    if invalid_entries:
        print("Found invalid entries in the index file:")
        for i, abs_wav, trn_file in invalid_entries:
            print(f"Entry {i}: wav={abs_wav}, trn={trn_file}")
    else:
        print("All entries in the index file are valid.")


class MASRDataset(Dataset):
    def __init__(self, index_path, labels_path):
        # Вызов функции проверки
        # 调用验证函数
        validate_index_file(index_path)

        with open(index_path) as f:
            idx = f.readlines()
        idx = [x.strip().split(",", 1) for x in idx]

        # Проверка и очистка путей, чтение содержимого .trn файлов как текста транскрипции
        # 验证并清理路径，同时读取 .trn 文件的内容作为转录文本
        self.idx = []
        for i, (wav, _) in enumerate(idx):
            abs_wav = os.path.abspath(wav)
            trn_file = abs_wav + ".trn"
            if os.path.exists(abs_wav) and os.path.exists(trn_file):
                with open(trn_file, 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
                self.idx.append((abs_wav, transcript))
            else:
                print(f"Warning: Missing file {abs_wav} or {trn_file}")

        print(f"Loaded dataset with {len(self.idx)} valid files.")

        labels = joblib.load(labels_path)
        self.labels = dict([(labels[i], i) for i in range(len(labels))])
        self.labels_str = labels

    def __getitem__(self, index):
        wav, transcript = self.idx[index]
        print(f"Attempting to load audio file: {wav}")  # Отладочный вывод
                                                         # 调试输出
        try:
            wav_data = load_audio(wav)
        except Exception as e:
            print(f"Failed to load audio file {wav}: {e}")
            raise
        
        spect = spectrogram(wav_data)
        transcript = list(filter(None, [self.labels.get(x) for x in transcript]))

        return spect, transcript

    def __len__(self):
        return len(self.idx)


def _collate_fn(batch):
    def func(p):
        return p[0].size(1)

    # Сортировка батча по длине последовательности в порядке убывания
    batch = sorted(batch, key=lambda sample: sample[0].size(1), reverse=True)
    longest_sample = max(batch, key=func)[0]
    freq_size = longest_sample.size(0)
    minibatch_size = len(batch)
    max_seqlength = longest_sample.size(1)
    inputs = torch.zeros(minibatch_size, freq_size, max_seqlength)
    input_lens = torch.IntTensor(minibatch_size)
    target_lens = torch.IntTensor(minibatch_size)
    targets = []
    for x in range(minibatch_size):
        sample = batch[x]
        tensor = sample[0]
        target = sample[1]
        seq_length = tensor.size(1)
        inputs[x].narrow(1, 0, seq_length).copy_(tensor)
        input_lens[x] = seq_length
        target_lens[x] = len(target)
        targets.extend(target)
    targets = torch.IntTensor(targets)
    return inputs, targets, input_lens, target_lens


class MASRDataLoader(DataLoader):
    def __init__(self, *args, **kwargs):
        super(MASRDataLoader, self).__init__(*args, **kwargs)
        # Установка пользовательской функции объединения для DataLoader
        self.collate_fn = _collate_fn
