from __future__ import annotations

from .tokens import Token, TokenType


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens = []

        while self.position < len(self.source):
            char = self.source[self.position]

            if char == "{":
                if self._peek(1) == "{":
                    if self._peek(2) == "{":
                        tokens.append(self._tokenize_comment())
                    else:
                        tokens.append(self._tokenize_variable())
                elif self._peek(1) == "%":
                    tokens.append(self._tokenize_statement())
                else:
                    tokens.append(self._tokenize_text())
            else:
                tokens.append(self._tokenize_text())

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _peek(self, offset: int = 1) -> str:
        pos = self.position + offset
        if pos >= len(self.source):
            return ""
        return self.source[pos]

    def _tokenize_text(self) -> Token:
        start = self.position
        start_line = self.line
        start_column = self.column

        while self.position < len(self.source):
            if self.source[self.position] == "{":
                if self._peek(1) == "{" or self._peek(1) == "%":
                    break
            if self.source[self.position] == "\n":
                self.line += 1
                self.column = 1
            self.position += 1

        text = self.source[start:self.position]
        return Token(TokenType.TEXT, text, start_line, start_column)

    def _tokenize_variable(self) -> Token:
        start = self.position
        start_line = self.line
        start_column = self.column

        self.position += 2
        depth = 1

        while self.position < len(self.source):
            if self.source[self.position] == "}":
                if self._peek(1) == "}":
                    self.position += 1
                    depth -= 1
                    if depth == 0:
                        self.position += 1
                        break
            elif self.source[self.position] == "{":
                if self._peek(1) == "{":
                    depth += 1
                    self.position += 1
            elif self.source[self.position] == "\n":
                self.line += 1
                self.column = 1
            self.position += 1

        expr = self.source[start + 2:self.position - 2].strip()
        return Token(TokenType.VARIABLE, expr, start_line, start_column)

    def _tokenize_statement(self) -> Token:
        start = self.position
        start_line = self.line
        start_column = self.column

        self.position += 2
        depth = 1

        while self.position < len(self.source):
            if self.source[self.position] == "%":
                if self._peek(1) == "}":
                    self.position += 1
                    depth -= 1
                    if depth == 0:
                        self.position += 1
                        break
            elif self.source[self.position] == "{":
                if self._peek(1) == "%":
                    depth += 1
                    self.position += 1
            elif self.source[self.position] == "\n":
                self.line += 1
                self.column = 1
            self.position += 1

        expr = self.source[start + 2:self.position - 2].strip()
        return Token(TokenType.STATEMENT, expr, start_line, start_column)

    def _tokenize_comment(self) -> Token:
        start = self.position
        start_line = self.line
        start_column = self.column

        self.position += 3

        while self.position < len(self.source):
            if self.source[self.position] == "}":
                if self._peek(1) == "}" and self._peek(2) == "}":
                    self.position += 3
                    break
            elif self.source[self.position] == "\n":
                self.line += 1
                self.column = 1
            self.position += 1

        comment = self.source[start + 3:self.position - 3].strip()
        return Token(TokenType.COMMENT, comment, start_line, start_column)
