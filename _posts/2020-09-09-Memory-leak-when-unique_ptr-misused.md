---
layout: post 
title:  "Memory leak when unique_ptr misused."
date:   2020-08-09 16:50:47 +0900
categories: Programming 
tags: c++ memory_leak 
---

<https://github.com/jaxonwang/thallium/commit/e7f51e391d05098666ec9123b8bbf9b9f44a2cc7>

```cpp
unique_ptr p{new int[10]{}}; ///!!!
```

Stupid but need to be carefull enough.

std::make_unique in c++14 is prefered:

```cpp
make_unique<int[]>(10);
```
This will make 10 size array of int
