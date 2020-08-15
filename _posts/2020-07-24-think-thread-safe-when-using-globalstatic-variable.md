---
layout: post
title: "think thread safe when using global/static variable"
categories: Programming 
date:   2020-07-24 16:50:47 +0900
tags: thread-safe c++ concurrent
---

```cpp
const char *get_file_name(const char *path) {
    // get the file name for __FILE__ macro
    //  should be thread safe
    static thread_local unordered_map dict;
    if (dict.count(path) == 0) {
        const char *pos = strrchr(path, '/') ? strrchr(path, '/') + 1 : path;
        dict[path] = pos;
    }
    return dict[path];
}
```

this is a function to get the filename of the source file, will be invoked every log() call

without thread_local, SEGV!


