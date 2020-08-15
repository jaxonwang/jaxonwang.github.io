---
layout: post 
title:  "坑! Pitfall: C++ tepmlate dependent name lookup"
date:   2020-07-28 16:50:47 +0900
categories: Programming 
tags: c++ cpp_template
---

Recently I wrote some code like below:


```cpp
#include

using namespace std;

inline size_t build_buf_size() {
    return 0;
}

template
size_t build_buf_size(const string &t1, const T1 & args) {
    int i = 0;
    return t1.size() + build_buf_size(i, args);
}

template
size_t build_buf_size(const T &t, const T1 &t1) {
    return sizeof(t1) + sizeof(t);
}

int main(int argc, const char *argv[])
{
    int a, b, c,d;
    string f{"123ffffffffff"};
    cout << build_buf_size(f, c) << endl;
    return 0;
}
```

This yields compiling error:

```console
./test1.cc: In instantiation of ‘size_t build_buf_size(const string&, const T1&) [with T1 = int; size_t = long unsigned int; std::__cxx11::string = std::__cxx11::basic_string<char>]’:
./test1.cc:24:32:   required from here
./test1.cc:12:38: error: no matching function for call to ‘build_buf_size(int&, const int&)’
     return t1.size() + build_buf_size(i, args);
                        ~~~~~~~~~~~~~~^~~~~~~~~
./test1.cc:5:15: note: candidate: size_t build_buf_size()
 inline size_t build_buf_size() {
               ^~~~~~~~~~~~~~
./test1.cc:5:15: note:   candidate expects 0 arguments, 2 provided
./test1.cc:10:8: note: candidate: template<class T1> size_t build_buf_size(const string&, const T1&)
 size_t build_buf_size(const string &t1, const T1 & args) {
        ^~~~~~~~~~~~~~
./test1.cc:10:8: note:   template argument deduction/substitution failed:
./test1.cc:12:38: note:   cannot convert ‘i’ (type ‘int’) to type ‘const string& {aka const std::__cxx11::basic_string<char>&}’
     return t1.size() + build_buf_size(i, args);
                        ~~~~~~~~~~~~~~^~~~~~~~~
```


Where we can see the compiler just ignores the candidate `template <class T, class... T1> build_buf_size`

Why?

OKay… what my idea was that, `build_buf_size` in `template<class... T1> build_buf_size` is a dependent name, so the name lookup(find the declaration of the name) should be at the time when the compiler tries to do build_buf_size template instantiation at the second time compiling (Two-Phase Lookup), so the compiler should have already known the declaration of `template <class T, class... T1> build_buf_size`.

But actually, the dependent name lookup rules(<https://en.cppreference.com/w/cpp/language/dependent_name>) requires that “non-ADL lookup examines function declarations with external linkage that are visible from the template definition context”. That’s why the compiler ignores the third build_buf_size……

To solve that issue, just:


```cpp
inline size_t build_buf_size() {
    return 0;
}
template  //add declaration here!
size_t build_buf_size(const T &t1, T1 &... args);
template
size_t build_buf_size(const string &t1, T1 &... args) {
    return t1.size() + build_buf_size(args...);
}
template
size_t build_buf_size(const T &t1, T1 &... args) {
    return sizeof(t1) + build_buf_size(args...);
}
```

That took me a long time to figure out what is going on exactly. C++ is a language that you need to dig very deep for an explanation even for some problems that every c++ beginners will encounter…
