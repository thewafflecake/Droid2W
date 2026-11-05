#include <dlfcn.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <utils/Log.h>
void *dlopen(const char *path,int flags){
 static void *(*real_dlopen)(const char *,int);
 if(!real_dlopen)real_dlopen=dlsym(RTLD_DEFAULT,"dlopen");
 if(!real_dlopen){ALOGE("Droid2W app redirect: cannot resolve real dlopen");return NULL;}
 if(path && getuid()>=10000 && getenv("DROID2W_GPU_TEST") &&
    !strcmp(path,"/system/lib/egl/libGLES.so")){
  ALOGI("Droid2W per-app EGL redirect, uid=%u pid=%d",(unsigned)getuid(),getpid());
  return real_dlopen("/data/local/tmp/zero2w-multimedia/libGLES_app_test.so",flags);
 }
 return real_dlopen(path,flags);
}
