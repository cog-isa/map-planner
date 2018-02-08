(define (domain logistics)
	(:requirements :typing :multi-agent)
(:types
	location vehicle package city weight - object
	airport - location
	truck - vehicle
)
(:predicates
	(at ?obj - object ?loc - location)
	(in ?obj - package ?veh - vehicle)
	(in-city ?loc - location ?city - city)
	(empty ?veh - vehicle)
	(cargo ?w - weight ?obj - package)
)

(:action load-truck
	:agent (?truck - truck)
	:parameters (?obj - package ?loc - location ?veh - vehicle ?w - weight)
	:precondition (and
		(at ?truck ?loc)
		(at ?obj ?loc)
		(cargo ?w ?obj)
		(empty ?veh)
	)
	:effect (and
		(not (at ?obj ?loc))
		(not (empty ?veh))
		(in ?obj ?truck)
		(at ?truck ?loc)
		(cargo ?w ?obj)
	)
)


(:action unload-truck
	:agent (?truck - truck)
	:parameters (?obj - package ?loc - location ?veh - vehicle ?w - weight)
	:precondition (and
		(at ?truck ?loc)
		(in ?obj ?truck)
		(cargo ?w ?obj)
	)
	:effect (and
		(not (in ?obj ?truck))
		(at ?obj ?loc)
		(empty ?veh)
		(at ?truck ?loc)
		(cargo ?w ?obj)
	)
)


(:action drive-truck
	:agent (?truck - truck)
	:parameters (?loc-from - location ?loc-to - location ?city - city)
	:precondition (and
		(at ?truck ?loc-from)
	)
	:effect (and
		(not (at ?truck ?loc-from))
		(at ?truck ?loc-to)
	)
)

)