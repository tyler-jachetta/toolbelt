#!/usr/bin/env bats

SOURCE_FN="test_cfg.vtc"
EXPECTED="expected.tavern.yaml"
EXPECTED_WITH_COMMENTS="expected-with-comment.tavern.yaml"
OUTFILE="out.tavern.yaml"
SOURCEFILES_DIR="tests/convert_vtc"

setup() {
    export TEMPDIR=$(mktemp -d)
    # put temp files in place
    for file in "$SOURCE_FN" "$EXPECTED" "${EXPECTED_WITH_COMMENTS}"; do
        cp "${SOURCEFILES_DIR}/${file}" "${TEMPDIR}/${file}"
    done

}

teardown() {
    rm -rf "${TEMPDIR}"
}

@test "convert_file_to_file" {
    
    ./convert_vtc.py --debug "${TEMPDIR}/${SOURCE_FN}" "${TEMPDIR}/${OUTFILE}"
    diff -q "${TEMPDIR}/${EXPECTED}" "${TEMPDIR}/${OUTFILE}"
}
@test "convert_file_into_dir" {
    
    ./convert_vtc.py "${TEMPDIR}/${SOURCE_FN}" "${TEMPDIR}/${OUTFILE}"
    diff -q "${TEMPDIR}/${EXPECTED}" "${TEMPDIR}/${OUTFILE}"
}
@test "convert dir into dir" {
    
    ./convert_vtc.py --debug "${TEMPDIR}" "${TEMPDIR}"
    yq compare -q "${TEMPDIR}/${EXPECTED}" "${TEMPDIR}/${OUTFILE}"
}

@test "convert all files in a dir" {
    ./convert_vtc.py "${TEMPDIR}"
    diff -q "${TEMPDIR}/${EXPECTED}" "${TEMPDIR}/${OUTFILE}"
}