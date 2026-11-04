#!/usr/bin/env python3
"""Generate a small PCM output HAL from the Apache-licensed KitKat template."""
from pathlib import Path
root = Path(__file__).resolve().parent
source = root / 'aosp/hardware/libhardware/modules/audio/audio_hw.c'
target = root / 'aosp/device/experimental/zero2w/audio'
target.mkdir(exist_ok=True)
text = source.read_text().replace('audio_hw_default', 'audio_hw_zero2w')
text = text.replace('#include <hardware/audio.h>', '#include <hardware/audio.h>\n#include <tinyalsa/asoundlib.h>\n#include <cutils/properties.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>')
text = text.replace('    struct audio_stream_out stream;\n', '''    struct audio_stream_out stream;
    pthread_mutex_t lock;
    struct pcm *pcm;
    int reported_error;
''')
text = text.replace('return 44100;', 'return 48000;').replace('return 4096;', 'return 2048;')
def replace_function(name, body):
    global text
    start = text.index('{', text.index(name + '('))
    level = 1
    end = start + 1
    while level:
        level += (text[end] == '{') - (text[end] == '}')
        end += 1
    text = text[:start] + '{\n' + body + '\n}' + text[end:]
replace_function('out_set_sample_rate', '    return rate == 48000 ? 0 : -EINVAL;')
replace_function('out_set_format', '    return format == AUDIO_FORMAT_PCM_16_BIT ? 0 : -EINVAL;')
replace_function('out_standby', '''    struct stub_stream_out *out = (struct stub_stream_out *)stream;
    pthread_mutex_lock(&out->lock);
    if (out->pcm) pcm_close(out->pcm);
    out->pcm = NULL;
    pthread_mutex_unlock(&out->lock);
    return 0;''')
replace_function('out_get_latency', '    return 512 * 4 * 1000 / 48000;')
replace_function('out_set_volume', '    return -ENOSYS; /* AudioFlinger applies software volume. */')
replace_function('out_write', '''    struct stub_stream_out *out = (struct stub_stream_out *)stream;
    struct pcm_config cfg = { .channels = 2, .rate = 48000,
        .period_size = 512, .period_count = 4, .format = PCM_FORMAT_S16_LE };
    int failed = 0;
    pthread_mutex_lock(&out->lock);
    if (!out->pcm) {
        char value[PROPERTY_VALUE_MAX];
        property_get("persist.zero2w.audio.card", value, "0");
        int card = atoi(value);
        property_get("persist.zero2w.audio.device", value, "0");
        int device = atoi(value);
        if (card < 0 || card > 31 || device < 0 || device > 31) {
            failed = 1;
        } else {
            out->pcm = pcm_open(card, device, PCM_OUT, &cfg);
            if (!out->pcm || !pcm_is_ready(out->pcm)) failed = 1;
        }
    }
    if (!failed && pcm_write(out->pcm, buffer, bytes)) failed = 1;
    if (failed) {
        if (!out->reported_error)
            ALOGE("PCM output unavailable: %s", out->pcm ? pcm_get_error(out->pcm) : "invalid card/device");
        out->reported_error = 1;
        if (out->pcm) pcm_close(out->pcm);
        out->pcm = NULL;
    } else {
        out->reported_error = 0;
    }
    pthread_mutex_unlock(&out->lock);
    if (failed) usleep((uint64_t)bytes * 1000000 / 4 / 48000);
    return bytes;''')
text = text.replace('    out->stream.common.get_sample_rate = out_get_sample_rate;', '''    config->sample_rate = 48000;
    config->channel_mask = AUDIO_CHANNEL_OUT_STEREO;
    config->format = AUDIO_FORMAT_PCM_16_BIT;
    pthread_mutex_init(&out->lock, NULL);
    out->stream.common.get_sample_rate = out_get_sample_rate;''')
text = text.replace('    free(stream);', '''    out_standby(&stream->common);
    pthread_mutex_destroy(&((struct stub_stream_out *)stream)->lock);
    free(stream);''')
replace_function('adev_open_input_stream', '''    *stream_in = NULL;
    return -ENOSYS; /* No capture hardware has been brought up. */''')
(target / 'audio_hw.c').write_text(text)
(target / 'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := audio.primary.zero2w
LOCAL_MODULE_PATH := $(TARGET_OUT_SHARED_LIBRARIES)/hw
LOCAL_SRC_FILES := audio_hw.c
LOCAL_SHARED_LIBRARIES := liblog libcutils libtinyalsa
LOCAL_C_INCLUDES := external/tinyalsa/include
LOCAL_MODULE_TAGS := optional
include $(BUILD_SHARED_LIBRARY)
''')
print('Prepared zero2w PCM output HAL; no input or automatic I2S routing advertised.')
