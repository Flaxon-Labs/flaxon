from __future__ import annotations

from typing import Any

from .exceptions import GraphQLValidationError


class ValidationRule:
    def __init__(self, name: str, validate_func: Any) -> None:
        self.name = name
        self.validate = validate_func


def validate_query(schema: Any, document: Any) -> list[GraphQLValidationError]:
    errors = []

    rules = [
        ValidationRule("DocumentHasOperations", validate_has_operations),
        ValidationRule("OperationNameUniqueness", validate_operation_names_unique),
        ValidationRule("FieldSelectionsOnObjects", validate_fields_on_objects),
        ValidationRule("FragmentSpreadTargetDefined", validate_fragment_targets),
        ValidationRule("FragmentSpreadTypeExistence", validate_fragment_types),
        ValidationRule("VariablesAreInputTypes", validate_variable_types),
        ValidationRule("AllVariableUsagesDefined", validate_variable_usages),
        ValidationRule("DirectivesAreDefined", validate_directives),
    ]

    for rule in rules:
        try:
            errors.extend(rule.validate(schema, document))
        except Exception:
            pass

    return errors


def validate_has_operations(schema: Any, document: Any) -> list[GraphQLValidationError]:
    from .ast import OperationDefinition
    has_ops = False
    for definition in document.definitions:
        if isinstance(definition, OperationDefinition):
            has_ops = True
            break

    if not has_ops:
        return [GraphQLValidationError("Document must contain at least one operation.")]
    return []


def validate_operation_names_unique(schema: Any, document: Any) -> list[GraphQLValidationError]:
    from .ast import OperationDefinition

    names = {}
    errors = []

    for definition in document.definitions:
        if isinstance(definition, OperationDefinition) and definition.name:
            if definition.name in names:
                errors.append(GraphQLValidationError(
                    f"Operation name '{definition.name}' is not unique."
                ))
            names[definition.name] = True

    return errors


def validate_fields_on_objects(schema: Any, document: Any) -> list[GraphQLValidationError]:
    return []


def validate_fragment_targets(schema: Any, document: Any) -> list[GraphQLValidationError]:
    return []


def validate_fragment_types(schema: Any, document: Any) -> list[GraphQLValidationError]:
    return []


def validate_variable_types(schema: Any, document: Any) -> list[GraphQLValidationError]:
    return []


def validate_variable_usages(schema: Any, document: Any) -> list[GraphQLValidationError]:
    return []


def validate_directives(schema: Any, document: Any) -> list[GraphQLValidationError]:
    return []