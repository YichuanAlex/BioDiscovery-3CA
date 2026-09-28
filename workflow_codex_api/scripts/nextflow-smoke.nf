nextflow.enable.dsl = 2

process localSmoke {
    output:
    stdout

    script:
    """
    printf 'NEXTFLOW_LOCAL_OK\\n'
    """
}

workflow {
    localSmoke()
}
