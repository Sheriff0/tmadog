.PHONY: all default enterprise user;

OUTPUT = .

SRC = src

SHELL := $(shell which bash)

MAIN_DEP = ansm.m4 \
	   cookie_parse.m4 \
	   dbm.m4 \
	   dogrc.m4 \
	   dogs.m4 \
	   hack.m4 \
	   if.m4 \
	   main.m4 \
	   mkconfig.m4 \
	   navigation.m4 \
	   qstm.m4 \
	   scrm.m4 \
	   tmadog.m4 \
	   tmadog_utils.m4 \

M4FLAGS = -I $(SRC) -I .

$(shell mkdir -p $(OUTPUT)) 

all: default user enterprise ;

default: $(addprefix $(OUTPUT)/def_,$(MAIN_DEP:.m4=.py)) ;

enterprise: $(addprefix $(OUTPUT)/ent_,$(MAIN_DEP:.m4=.py));

user: $(addprefix $(OUTPUT)/usr_,$(MAIN_DEP:.m4=.py));

$(OUTPUT)/def_%.py: $(SRC)/%.m4
	m4 $(M4FLAGS) -DLIBPREFIX=def_ $< > $@

$(OUTPUT)/usr_%.py: $(SRC)/%.m4
	@echo $@ from $<

$(OUTPUT)/ent_%.py: $(SRC)/%.m4
	@echo $@ from $<

