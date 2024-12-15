// 兼容性处理
window.URL = window.URL || window.webkitURL;

// 创建录音机类
var HZRecorder = function (stream, config) {
    config = config || {};
    config.sampleBits = config.sampleBits || 16;      // 采样数位：8, 16
    config.sampleRate = config.sampleRate || 16000;   // 采样率：16000

    // 创建音频环境对象
    var audioContext = window.AudioContext || window.webkitAudioContext;
    var context = new audioContext();
    var audioInput = context.createMediaStreamSource(stream);

    // 创建音频处理节点
    var recorder = context.createScriptProcessor(4096, 1, 1); // 单声道

    // 音频数据管理
    var audioData = {
        size: 0,
        buffer: [],
        inputSampleRate: context.sampleRate,
        inputSampleBits: 16,
        outputSampleRate: config.sampleRate,
        outputSampleBits: config.sampleBits,

        input: function (data) {
            this.buffer.push(new Float32Array(data));
            this.size += data.length;
        },

        compress: function () {
            var data = new Float32Array(this.size);
            var offset = 0;
            for (var i = 0; i < this.buffer.length; i++) {
                data.set(this.buffer[i], offset);
                offset += this.buffer[i].length;
            }
            var compression = parseInt(this.inputSampleRate / this.outputSampleRate);
            var length = data.length / compression;
            var result = new Float32Array(length);
            var index = 0, j = 0;
            while (index < length) {
                result[index] = data[j];
                j += compression;
                index++;
            }
            return result;
        },

        encodeWAV: function () {
            var sampleRate = Math.min(this.inputSampleRate, this.outputSampleRate);
            var sampleBits = Math.min(this.inputSampleBits, this.outputSampleBits);
            var bytes = this.compress();
            var dataLength = bytes.length * (sampleBits / 8);
            var buffer = new ArrayBuffer(44 + dataLength);
            var view = new DataView(buffer);

            var writeString = function (str, offset) {
                for (var i = 0; i < str.length; i++) {
                    view.setUint8(offset + i, str.charCodeAt(i));
                }
            };

            writeString('RIFF', 0);
            view.setUint32(4, 36 + dataLength, true);
            writeString('WAVE', 8);
            writeString('fmt ', 12);
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true);
            view.setUint16(22, 1, true);
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * (sampleBits / 8), true);
            view.setUint16(32, sampleBits / 8, true);
            view.setUint16(34, sampleBits, true);
            writeString('data', 36);
            view.setUint32(40, dataLength, true);

            if (sampleBits === 8) {
                for (var i = 0; i < bytes.length; i++) {
                    var val = bytes[i] * 128 + 128;
                    view.setUint8(44 + i, val, true);
                }
            } else {
                for (var i = 0; i < bytes.length; i++) {
                    view.setInt16(44 + i * 2, bytes[i] * 32768, true);
                }
            }

            return new Blob([view], { type: 'audio/wav' });
        }
    };

    this.start = function () {
        audioInput.connect(recorder);
        recorder.connect(context.destination);
        console.log("录音已开始");
    };

    this.stop = function () {
        recorder.disconnect();
        console.log("录音已停止");
    };

    this.getBlob = function () {
        this.stop();
        return audioData.encodeWAV();
    };

    this.play = function (audio) {
        const blob = this.getBlob();
        if (!blob) {
            console.error("音频数据为空，无法播放");
            return;
        }
        const audioURL = window.URL.createObjectURL(blob);
        audio.src = audioURL;
        audio.load();
        audio.play().catch(error => console.error("播放录音失败: ", error));
        console.log("正在播放录音");
    };

    this.upload = function (url, callback) {
        const blob = this.getBlob();
        if (!blob) {
            console.error("音频数据为空，无法上传");
            return;
        }
        var fd = new FormData();
        fd.append("audio", blob);
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url);

        if (callback) {
            xhr.upload.addEventListener("progress", function (e) {
                const percentComplete = Math.round((e.loaded / e.total) * 100) + "%";
                callback('uploading', percentComplete);
            }, false);

            xhr.addEventListener("load", function () {
                callback('ok', xhr);
            }, false);

            xhr.addEventListener("error", function () {
                callback('error');
            }, false);

            xhr.addEventListener("abort", function () {
                callback('cancel');
            }, false);
        }

        xhr.send(fd);
        console.log("录音数据已上传");
    };

    recorder.onaudioprocess = function (e) {
        audioData.input(e.inputBuffer.getChannelData(0));
    };
};

HZRecorder.canRecording = !!navigator.mediaDevices.getUserMedia;

HZRecorder.get = function (callback, config) {
    if (!HZRecorder.canRecording) {
        alert('当前浏览器不支持录音功能！');
        return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
        const rec = new HZRecorder(stream, config);
        callback(rec);
    }).catch(function (error) {
        console.error('无法获取麦克风权限:', error);
        alert('无法获取麦克风权限，请检查浏览器设置！');
    });
};
