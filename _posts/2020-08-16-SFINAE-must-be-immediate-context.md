---
layout: post
title: "SFINAE must be in the immediate context"
date: 2020-08-16 09:57:44 +0900
categories: Programming 
tags: c++ cpp_template SFINAE
---

SFINAE is the provides the essential "Patten matching" like feature to C++ template meta-programming.

```cpp
template <class T> size_t haha(const T &t) { return t.size(); }

template <class T> void func(const T &t) { cout << "func" << endl; }

template <class T> void func(T &&t) { cout << haha(t) << endl; }

int main(int argc, const char *argv[]) {
  int i = 0;
  func(i);
  return 0;
}
```

Compiler says:

```console
./test.cc:10:13: error: member reference base type 'const int' is not a structure or union
    return t.size();
           ~^~~~~
./test.cc:20:13: note: in instantiation of function template specialization 'haha<int>' requested here
    cout << haha(t) << endl;
            ^
./test.cc:26:5: note: in instantiation of function template specialization 'func<int &>' requested here
    func(i);
    ^
1 error generated.
```

`T &&` matches `int` better than `const T &` as we can see. But the compiler does not try the `template <class T> size_t haha(const T &t)`, since this is not SFINAE!

from [cppreference](https://en.cppreference.com/w/cpp/language/sfinae):

> Only the failures in the types and expressions in the immediate context of the function type or its template parameter types or its explicit specifier (since C++20) are SFINAE errors. If the evaluation of a substituted type/expression causes a side-effect such as instantiation of some template specialization, generation of an implicitly-defined member function, etc, errors in those side-effects are treated as hard errors.

There is no SFINAE here, so there is a error. That's a common mistake when writing c++ template functions for a beginner (Yes, it's me!).
