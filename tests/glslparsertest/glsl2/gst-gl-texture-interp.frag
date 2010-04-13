/*
 * GStreamer
 * Copyright (C) 2008 Filippo Argiolas <filippo.argiolas@gmail.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#extension GL_ARB_texture_rectangle : enable
uniform sampler2DRect base;
uniform sampler2DRect blend;
uniform sampler2DRect alpha;
uniform float final_width, final_height;
uniform float base_width, base_height;
/*
uniform float blend_width, blend_height;
uniform float alpha_width, alpha_height;
*/
void main () {
vec2 base_scale = vec2 (base_width, base_height) / vec2 (final_width, final_height);
/*
vec2 blend_scale = vec2 (blend_width, blend_height) / vec2 (final_width, final_height);
vec2 alpha_scale = vec2 (alpha_width, alpha_height) / vec2 (final_width, final_height);
*/

vec4 basecolor = texture2DRect (base, gl_TexCoord[0].st * base_scale);
vec4 blendcolor = texture2DRect (blend, gl_TexCoord[0].st);
vec4 alphacolor = texture2DRect (alpha, gl_TexCoord[0].st);
gl_FragColor = (alphacolor * blendcolor) + (1.0 - alphacolor) * basecolor;
}
