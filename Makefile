# setapp
# Copyright 2020
# Al Danial
# Tom Kowalski

appname  := setapp
CXX      := g++
CXXFLAGS := -std=c++11 -Wall -g -O0
LDFLAGS  :=
LDLIBS   := -lfmt -lyaml-cpp -lboost_program_options -lboost_filesystem -lboost_system
RM       := /bin/rm
srcfiles := $(shell find . -name "*.C")
objects  := $(patsubst %.C, %.o, $(srcfiles))

all: $(appname)

$(appname): $(objects)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $(appname) $(objects) $(LDLIBS)

depend: .depend

.depend: $(srcfiles)
	$(RM) -f ./.depend
	$(CXX) $(CXXFLAGS) -MM $^>>./.depend;

clean:
	$(RM) -f $(objects)

dist-clean: clean
	$(RM) -f .depend

include .depend
