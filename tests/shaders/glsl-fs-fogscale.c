/*
 * Copyright © 2013 Henri Verbeet <hverbeet@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice (including the next
 * paragraph) shall be included in all copies or substantial portions of the
 * Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

/** @file glsl-fs-fogscale.c
 *
 * Tests that gl_Fog.scale is equivalent to
 * "1.0 / (gl_Fog.end - gl_Fog.start)" when fog start and end are equal. The
 * expectation is that 1.0 / 0.0 will produce a value similar to +INF. This
 * takes into account that some GPUs may not have a representation for INF.
 */

#include "piglit-util-gl.h"

PIGLIT_GL_TEST_CONFIG_BEGIN

	config.supports_gl_compat_version = 20;

	config.window_visual = PIGLIT_GL_VISUAL_RGBA | PIGLIT_GL_VISUAL_DOUBLE;

PIGLIT_GL_TEST_CONFIG_END

const char * tests[4] = { "vs and fs", "gs-out and fs", "vs, gs and fs", NULL };

static const char vs_source[] =
	"void main()\n"
	"{\n"
	"	gl_Position = gl_Vertex;\n"
	"	gl_FogFragCoord = gl_Position.x;\n"
	"}\n";

static const char *dummy_vs_source =
	"void main()\n"
	"{\n"
	"	gl_Position = gl_Vertex;\n"
	"}\n";

static const char fs_source[] =
	"void main()\n"
	"{\n"
	"	gl_FragColor = vec4(gl_FogFragCoord * gl_Fog.scale * vec2(1.0, -1.0), 0.0, 1.0);\n"
	"}\n";

static bool
test_prog(unsigned prog, const char *test_name)
{
	static const float green[] = {0.0f, 1.0f, 0.0f, 1.0f};
	static const float red[] = {1.0f, 0.0f, 0.0f, 1.0f};
	bool pass = true;

	glUseProgram(prog);

	glClearColor(0.0, 0.0, 1.0, 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	piglit_draw_rect(-1, -1, 2, 2);
	pass = piglit_probe_rect_rgba(0, 0,
				      piglit_width / 2, piglit_height,
				      green) && pass;
	pass = piglit_probe_rect_rgba(piglit_width / 2, 0,
				      piglit_width / 2, piglit_height,
				      red) && pass;

	piglit_report_subtest_result(pass ? PIGLIT_PASS : PIGLIT_FAIL, "%s",
				     test_name);

	return pass;
}

static void
create_gs_source(char **gs_source, char *fogFragCoordValue)
{
	(void)!asprintf(gs_source,
		"#version 150 compatibility\n"
		"layout(triangles) in;\n"
		"layout(triangle_strip, max_vertices = 3) out;\n"
		"\n"
		"void main()\n"
		"{\n"
		"	for (int i = 0; i < 3; i++) {\n"
		"		gl_Position = gl_in[i].gl_Position;\n"
		"		gl_FogFragCoord = %s;\n"
		"		EmitVertex();\n"
		"	}\n"
		"}\n",
		fogFragCoordValue);
}

enum piglit_result
piglit_display(void)
{
	bool pass = true;
	char *gs_source;
	char *gs_source2;

	/* Test simple vs and fs program */
	GLuint prog = piglit_build_simple_program(vs_source, fs_source);
	test_prog(prog, tests[0]);

	/* Test passing gl_FogFragCoord via the Geometry Shader */
	if (piglit_get_gl_version() >= 32) {
		/* Test gl_FogFragCoord gs output only */
		create_gs_source(&gs_source, "gl_Position.x");
		prog = piglit_build_simple_program_multiple_shaders(
			GL_VERTEX_SHADER, dummy_vs_source,
			GL_GEOMETRY_SHADER, gs_source,
			GL_FRAGMENT_SHADER, fs_source,
			0);
		pass = pass && test_prog(prog, tests[1]);

		/* Test gl_FogFragCoord both as a gs output and input */
		create_gs_source(&gs_source2, "gl_in[i].gl_FogFragCoord");
		prog = piglit_build_simple_program_multiple_shaders(
			GL_VERTEX_SHADER, vs_source,
			GL_GEOMETRY_SHADER, gs_source2,
			GL_FRAGMENT_SHADER, fs_source,
			0);
		pass = pass && test_prog(prog, tests[2]);

	} else {
		piglit_report_subtest_result(PIGLIT_SKIP, tests[1]);
		piglit_report_subtest_result(PIGLIT_SKIP, tests[2]);
	}

	return pass ? PIGLIT_PASS : PIGLIT_FAIL;
}

void
piglit_init(int argc, char **argv)
{
	piglit_register_subtests(tests);

	glFogf(GL_FOG_START, 0.0f);
	glFogf(GL_FOG_END, 0.0f);
}
