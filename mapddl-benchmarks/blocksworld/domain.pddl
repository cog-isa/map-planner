(define (domain blocks)
	(:requirements :typing :multi-agent :unfactored-privacy)
(:types
	agent block - object
)
(:predicates
	(on ?x - block ?y - block)
	(ontable ?x - block)
	(clear ?x - block)
    (holding ?ag - agent ?x - block)
    (handempty ?ag - agent)
)

(:action pick-up
	:parameters (?ag - agent ?x - block)
	:precondition (and
		(clear ?x)
		(ontable ?x)
		(handempty ?ag)
	)
	:effect (and
		(not (ontable ?x))
		(not (clear ?x))
		(not (handempty ?ag))
		(holding ?ag ?x)
	)
)


(:action put-down
	:parameters (?ag - agent ?x - block)
	:precondition 
		(holding ?ag ?x)
	:effect (and
		(not (holding ?ag ?x))
		(clear ?x)
		(handempty ?ag)
		(ontable ?x)
	)
)


(:action stack
	:parameters (?ag - agent ?x - block ?y - block)
	:precondition (and
		(holding ?ag ?x)
		(clear ?y)
	)
	:effect (and
		(not (holding ?ag ?x))
		(not (clear ?y))
		(clear ?x)
		(handempty ?ag)
		(on ?x ?y)
	)
)


(:action unstack
	:parameters (?ag - agent ?x - block ?y - block)
	:precondition (and
		(on ?x ?y)
		(clear ?x)
		(handempty ?ag)
	)
	:effect (and
		(holding ?ag ?x)
		(clear ?y)
		(not (clear ?x))
		(not (handempty ?ag))
		(not (on ?x ?y))
	)
)

)