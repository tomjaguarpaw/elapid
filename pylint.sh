# * no-member: pylint seems to have a lot of false positives
# * no-name-in-module: pylint seems to have a lot of false positives

pylint --reports=no \
       --ignore=GraphDebugger.py \
       --disable=all \
       --enable=E \
       --enable=F \
       --disable=no-member \
       --disable=no-name-in-module \
       --disable=not-context-manager \
       --enable=unused-variable \
       --enable=unused-argument \
       --enable=unused-import \
       --enable=undefined-variable \
       --enable=unbalanced-tuple-unpacking \
       --enable=relative-import \
       --enable=no-self-use \
       --enable=reimported \
       --enable=syntax-error \
       --enable=redefined-outer-name \
       --enable=unnecessary-pass \
       --enable=missing-final-newline \
       src/elapid/
