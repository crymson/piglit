// [config]
// expect_result: fail
// glsl_version: 1.30
// [end config]
//
// Check that 'filter' is a reserved keyword.

#version 130

int f()
{
	int filter;
	return 0;
}
