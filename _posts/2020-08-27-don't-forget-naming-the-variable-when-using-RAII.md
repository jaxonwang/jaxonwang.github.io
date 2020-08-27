---
layout: post
title: "don't forget naming the variable when using RAII"
date: 2020-08-27 13:25:57 +0900
categories: Programming
tags: cpp
---

RAII is an awesome design and very useful to accomplish tasks like "I want something automatically done and cleaned up nicely at the end of current scope".  
  

I use following class to temporally change the global state of logger and intercept all logs, for the log verifications in testing.  

```cpp  
class LoggingTracer{  
std::unique_ptr<LoggingTracerImpl> impl;  
public:  
// temporary set log level, and trace if not changelevelonly  
explicit LoggingTracer(const int level, bool changelevelonly);  
LoggingTracer(const LoggingTracer&) = delete;  
LoggingTracer(LoggingTracer&&) = delete;  
~LoggingTracer();  
std::vector<std::string> log_content();  
};  
```  

I try to replace the global object with a new one and switch it back when finished. The Logging tracer will hold the old object:  

```cpp  
LoggingTracer::LoggingTracer(const int level, const bool changelevelonly)  
: impl(new LoggingTracerImpl()) {  
impl->changelevelonly = changelevelonly;  
// store current  
thallium::get_global_manager().swap(impl->mnger_holder);  
}  
  
LoggingTracer::~LoggingTracer() {  
// revert to before  
thallium::get_global_manager().swap(impl->mnger_holder);  
}  
```  

Then I use `LoggingTracer` in a function:  

```cpp  
TEST(Coordinator, Register) {  
ti_test::LoggingTracer{1, true};  
// do the test  
}  
```  

But nothing that I intended happens after the construction of `LoggingTracer`...The first line doesn't work. Why? because I just forget to name that object, then it just immediately destruct!  
  
The correct way:
```cpp  
TEST(Coordinator, Register) {  
ti_test::LoggingTracer DONTFORGETME{1, true};  
// do the test  
}  
```  
Another silly mistake!
